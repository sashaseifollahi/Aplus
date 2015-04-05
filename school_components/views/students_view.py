from django.views import generic
from school_components.models import *
from accounts.models import TeacherUser
from accounts.utils import *
from school_components.forms.students_form import *
from school_components.utils import SchoolUtils
from django.shortcuts import render_to_response, redirect
from django.forms.models import model_to_dict
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.servers.basehttp import FileWrapper
from aplus.settings import SAMPLE_CSV_PATH
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib import messages
from django.shortcuts import redirect
import json
import csv
from django.contrib.auth.decorators import login_required

@login_required
def student_list(request, student_id=None):
	request = process_user_info(request)
	student_list = None

	if request.user_role == 'TEACHER':
		teacherID = request.user_profile.teachers.first().id
		student_list = Student.objects.filter(
			Q(enrolled_student__reg_class__classteacher__primary_teacher_id=teacherID) |
			Q(enrolled_student__reg_class__classteacher__secondary_teacher_id=teacherID))
		# teacher_user = TeacherUser.objects.get(user= request.user)
		# class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		# class_list = []
		# for c in class_teacher:
		# 	class_list.append(c.taught_class)
		# student_list=[]
		# for cl in class_list:
		# 	class_reg_list = ClassRegistration.objects.filter(reg_class=cl).order_by('student__last_name')
		# 	for item in class_reg_list:
		# 		student_list.append(item.student)
		form, student_list = student_list_helper(request, student_list)

	else:
		student_list = Student.objects.all()
		form, student_list = student_list_helper(request, student_list)
		

	context_dictionary = {
		'student_list': student_list,
		'student_filter': form,
		'view_form': StudentViewForm({'view': 'all' if request.GET.get('view', None) == 'all' else 'period'}),
	}

	if student_id:
		student = Student.objects.get(pk=student_id)
		context_dictionary['student'] = student
		
		class_list = [class_history_helper(class_reg) for class_reg in student.enrolled_student.all()]
		context_dictionary['class_history_list'] = class_list

	return render_to_response("students/student_list.html",
		context_dictionary,
		RequestContext(request))

# returns student list according to filters/period or total view
# also returns the form with fields populated with last filter
def student_list_helper(request, student_list):
	view = request.GET.get('view', None)

	if view is None or view == 'period':
		student_list = student_list.filter(
			school = request.user_school,
			enrolled_student__reg_class__period = request.user_period
		).annotate().order_by('last_name')
	elif view == 'all':
		student_list = Student.objects.filter(
			school = request.user_school
		).order_by('last_name')

	search_name = request.GET.get('name', None)
	search_phone = request.GET.get('phone_number', None)   
	form = StudentFilter({'name': search_name, 'phone_number': search_phone}) 

	if search_name:
		student_list = student_list.filter(
    		Q(first_name__icontains=search_name) | 
    		Q(last_name__icontains=search_name))

	if search_phone:
		student_list = student_list.filter(
			home_phone__icontains=search_phone)

	return form, student_list

'''
Delete Student
'''
@login_required
def delete_student_view (request, student_id):
    request = process_user_info(request)

    if (request.user_role == 'TEACHER'): 
			return render_to_response('404.html',RequestContext(request))

    student = Student.objects.get(pk=student_id)
    #deleting its parent info if not parent of other student
    if Student.objects.filter(parent=student.parent).count() == 1:
        Payment.objects.filter(parent=student.parent).delete()
        student.parent.delete()

    student.delete()
    messages.success(request, "Student has been deleted!")
    return redirect('school:studentlist')

@login_required
def student_edit(request, student_id):
	request = process_user_info(request)
	if (request.user_role == 'TEACHER'): 
			return render_to_response('404.html',RequestContext(request))

	student_list = Student.objects.all()

	# if request.user_role == 'TEACHER':
		# teacher_user = TeacherUser.objects.get(user= request.user)
		# class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		# class_list = []
		# for c in class_teacher:
		# 	class_list.append(c.taught_class)
		# student_list=[]
		# for cl in class_list:
		# 	class_reg_list = ClassRegistration.objects.filter(reg_class=cl).order_by('student__last_name')
		# 	for item in class_reg_list:
		# 		student_list.append(item.student)

	# else:
	
	form, student_list = student_list_helper(request, student_list)
		
	context_dictionary = {
		'student_list': student_list,
		'student_filter': form,
		'view_form': StudentViewForm({'view': 'all' if request.GET.get('view', None) == 'all' else 'period'}),
	}

	try:
		student = Student.objects.get(pk=student_id)
		
		if student.school != request.user_school:
                        raise ObjectDoesNotExist
                
		context_dictionary['student_id'] = student_id
		s = StudentForm(instance=student)
		s.fields['parent'].queryset = Parent.objects.filter(school=request.user_school)
		
		if request.method == 'POST':
                        s = StudentForm(request.POST, instance=student)
                        if s.is_valid():
                                s.save()
                                context_dictionary['succ']=True
                        
		context_dictionary['student_form'] = s
		
	except ObjectDoesNotExist:
                context_dictionary['error'] = 'There is no student with that id in this school.'
                
	return render_to_response("students/student_edit.html",
		context_dictionary,
		RequestContext(request))

# turn into a dict to help with sorting in UI
def class_history_helper(class_reg):
	m = model_to_dict(class_reg)
	m['period'] = class_reg.reg_class.period.description
	m['id'] = class_reg.reg_class.id
	m['class_name'] = class_reg.reg_class
	m['status'] = class_reg.registration_status
	return m

# returns student info, used on the registration page
@login_required
def student_get(request):
	request = process_user_info(request)
	if request.method == 'GET':
		student_id = request.GET['student_id']
		student = Student.objects.get(pk=student_id)
		student_json = serializers.serialize("json", [student])

		# get class history for student
		class_list = [class_reg for class_reg in 
			student.enrolled_student.all().order_by('reg_class__course')]
		context_dictionary = {'class_list': class_list }

		render_string = render_to_string(
			'registration/course_registration_classhistory.html',
			context_dictionary)

		student_json = json.loads(student_json)[0]['fields']
		student_json['class_history_html'] = render_string
		student_json_str = json.dumps(student_json)

		return HttpResponse(student_json_str, content_type="application/json")


# create a new student with form data
@login_required
def student_create(request):
	request = process_user_info(request)

	if (request.user_role == 'TEACHER'): 
			return render_to_response('404.html',RequestContext(request))


	s = StudentForm()
	s.fields['parent'].queryset = Parent.objects.filter(school=request.user_school)

	context_dictionary = { 'student_form': s }


	if request.method == 'POST':
		s = StudentForm(request.POST)

		if s.is_valid():
			student = s.save(commit=False)
			student.school = request.user_school
			student.period = request.user_period
			student.save()
			return HttpResponseRedirect(
					reverse('school:studentlist', args=(student.id,)))
		else:
			context_dictionary['errors'] = s.errors 

	return render_to_response('students/student_form.html',
		context_dictionary,
		RequestContext(request))


@login_required
def student_form(request):
        
	context_dictionary = {'student_form': StudentForm() }

	return render_to_response('students/student_form.html',
		context_dictionary,
		RequestContext(request))


# TODO: if file is too big, save to disk instead
# if time figure out a way to confirm
@login_required
def student_upload(request):
	request = process_user_info(request)
	if (request.user_role == 'TEACHER'): 
			return render_to_response('404.html',RequestContext(request))

	context_dictionary = {'form': StudentCSVForm()}
	form = StudentCSVForm(request.POST, request.FILES)
	
	if request.method == 'POST' and 'file' in request.FILES:
		#  check for errors
		errors = SchoolUtils.validate_csv(request.FILES['file'])

		if errors:
			context_dictionary['errors'] = errors
		else:
			# actually save
			s = request.user_school
			per = request.user_period
			student_list = SchoolUtils.parse_csv(request.FILES['file'], school=s, period=per)
			context_dictionary['student_list'] = student_list

	return render_to_response('students/student_upload.html',
		context_dictionary, RequestContext(request))

@login_required
def student_export(request):
	request = process_user_info(request)
	if (request.user_role == 'TEACHER'): 
			return render_to_response('404.html',RequestContext(request))
			
	context_dictionary = {}

	if request.method == 'POST':
		response = HttpResponse(content_type='text/csv')
		response['Content-Disposition'] = 'attachment; filename="students.csv"'

		students = Student.objects.all()
		writer = csv.writer(response)
		for student in students:
			writer.writerow(
				[student.first_name, student.last_name, student.gender, student.birthdate, 
				student.home_phone, student.parent, student.parent.cell_phone, student.parent.email, 
				student.allergies])

		return response
	else:
		return render_to_response('students/student_export.html',
			context_dictionary,
			RequestContext(request))

@login_required
def student_sample_csv(request):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="sample_students.csv"'
	
	f = open(SAMPLE_CSV_PATH)
	response.write(f.read())
	f.close()

	return response
