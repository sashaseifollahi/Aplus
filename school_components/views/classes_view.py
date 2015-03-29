
from school_components.models.classes_model import *
from school_components.models.students_model import Student
from school_components.forms.classes_form import *
from accounts.models import TeacherUser
from django.shortcuts import render_to_response
from django.shortcuts import render
from django.template import RequestContext
from django.db import IntegrityError
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from datetime import datetime
from dashboard.models import *

from django.forms.models import modelformset_factory
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth.decorators import login_required

@login_required
def class_list(request, class_id=None):

	if request.user.userprofile.role == 'TEACHER':
		teacher_user = TeacherUser.objects.get(user= request.user)
		class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		class_list = []
		for c in class_teacher:
			class_list.append(c.taught_class)
	else:

		class_list = Class.objects.filter(
			school = request.user.userprofile.school, 
			period = request.user.userprofile.period
		).order_by('course')

	search_course = request.GET.get('course', None)
	search_section = request.GET.get('section', None)  
	search_dept = request.GET.get('department', None)  
	
	if search_course:
		class_list = class_list.filter(
			course__name__icontains=search_course)

	if search_section:
		class_list = class_list.filter(
			section__icontains=search_section)

	if search_dept:
		class_list = class_list.filter(
			course__department__name__icontains=search_dept)

	context_dictionary = { 'class_list': class_list, 'class_filter': ClassFilter() }

	if class_id:
		try:
			c = Class.objects.get(pk=class_id)
			if c.school != request.user.userprofile.school or c.period != request.user.userprofile.period:
				raise ObjectDoesNotExist
			context_dictionary['class'] = c
		except ObjectDoesNotExist:
				context_dictionary['error'] = 'There is no class in this school and period with that id.'
	 
	return render_to_response("classes/class_list.html",
		context_dictionary,
		RequestContext(request))

@login_required
def class_create(request):
	class_form = ClassForm(prefix='info')
	class_form.fields['course'].queryset = Course.objects.filter(
		school = request.user.userprofile.school, 
		period = request.user.userprofile.period
	)

	# TODO: teacher will have period field
	teacher_form = ClassTeacherForm(prefix='te')
	teachers = TeacherUser.objects.filter(
		user__period = request.user.userprofile.period, 
		user__school = request.user.userprofile.school
	)
	teacher_form.fields['primary_teacher'].queryset = teachers
	teacher_form.fields['secondary_teacher'].queryset = teachers
   
	context_dictionary = {
		'class_form': class_form, 
		'classday_form': ClassScheduleForm(prefix='sch'),
		'classteacher_form': teacher_form
	}

	if request.method == 'POST':
		cf = ClassForm(request.POST, prefix='info')
		sf = ClassScheduleForm(request.POST, prefix='sch')
		te = ClassTeacherForm(request.POST, prefix='te')
                te.fields['primary_teacher'].queryset = teachers
                te.fields['secondary_teacher'].queryset = teachers
	
		if cf.is_valid() and sf.is_valid() and te.is_valid():
			# save class
			new = cf.save(commit=False)
			new.school = request.user.userprofile.school
			new.period = request.user.userprofile.period
			new.save()

			# save class schedule
			schedule = sf.save(commit=False)
			schedule.sch_class = new
			schedule.save()

			# save class teacher
			#try:
			
			teacher = te.save(commit=False)
			teacher.taught_class = new
			teacher.save()
			#except Exception as e:
				# no teacher in request, don't create ClassTeacher object
			#	pass

			return HttpResponseRedirect(
				reverse('school:classlist', args=(new.id,)))
		else:
			context_dictionary['class_errors'] = cf.errors
			context_dictionary['schedule_errors'] = sf.errors
			context_dictionary['teacher_errors'] = te.errors

                        context_dictionary['class_form']=cf
                        context_dictionary['classday_form']=sf
                        context_dictionary['classteacher_form']=te
                        
	return render_to_response('classes/class_form.html',
		context_dictionary,
		RequestContext(request))

@login_required
def class_edit(request, class_id):
		class_list = Class.objects.filter(
		school = request.user.userprofile.school, 
		period = request.user.userprofile.period).order_by('course')

		context_dictionary = {'class_list': class_list}

		try:
				c = Class.objects.get(pk=class_id)
				if c.school != request.user.userprofile.school or c.period != request.user.userprofile.period:
					raise ObjectDoesNotExist
			
				context_dictionary['class_id'] = class_id
				
                                        #context_dictionary['shalala'] = 'shalala'

                                s = c.schedule #all classes created normally (through the form) should have this...
                         
                                        #context_dictionary['here'] = 'here' #for testing

                                t = c.classteacher #class can only have one classteacher
                                       # context_dictionary['ha'] = 'ha'# for testing

				class_form = ClassForm(prefix='info', instance = c)
				classday_form = ClassScheduleForm(prefix='sch', instance = s)
				classteacher_form = ClassTeacherForm(prefix='te', instance = t)
				teachers = TeacherUser.objects.filter(user__school=request.user.userprofile.school, user__period=request.user.userprofile.period)
				classteacher_form.fields['primary_teacher'].queryset = teachers
				classteacher_form.fields['secondary_teacher'].queryset = teachers
	
				if request.method == 'POST':
						class_form = ClassForm(request.POST, prefix='info', instance = c)
						classday_form = ClassScheduleForm(request.POST, prefix='sch', instance = s)
						classteacher_form = ClassTeacherForm(request.POST, prefix='te', instance = t)

						teachers = TeacherUser.objects.filter(user__school=request.user.userprofile.school, user__period=request.user.userprofile.period)
                                                classteacher_form.fields['primary_teacher'].queryset = teachers
                                                classteacher_form.fields['secondary_teacher'].queryset = teachers
                                
						if class_form.is_valid() and classday_form.is_valid() and classteacher_form.is_valid():
								class_form.save()
								classday_form.save()
								classteacher_form.save()
								context_dictionary['succ']=True
								
				context_dictionary['class_form'] = class_form
				context_dictionary['classday_form'] = classday_form
				context_dictionary['classteacher_form'] = classteacher_form
				
		except ObjectDoesNotExist:
				context_dictionary['error'] = 'There is no class in this school and period with that id.'
						
		return render_to_response("classes/class_edit.html",context_dictionary,RequestContext(request))

@login_required
def class_registration(request, class_id=None):
	if request.POST:
		return class_registration_helper(request, class_id)

	else:
		class_list = Class.objects.filter(
			school = request.user.userprofile.school, 
			period = request.user.userprofile.period).order_by('course')
		context_dictionary = {'class_list': class_list }

		if class_id:
			cl = Class.objects.get(pk=class_id)
			context_dictionary['class'] = cl 
			context_dictionary['student_list'] = Student.objects.filter(
				school = request.user.userprofile.school
			)
			context_dictionary['form'] = ClassRegistrationForm()
			context_dictionary['remove_form'] = RemoveClassRegistrationForm()
		
		return render_to_response("classes/class_registration.html",
			context_dictionary,
			RequestContext(request))

# register student to class
@login_required
def class_registration_helper(request, class_id):
	student_id = request.POST['student_id']
	student = Student.objects.get(pk=student_id)
	
	# check if on waiting list
	reg = student.enrolled_student.filter(reg_class__id=class_id)
	if len(reg) > 0:
		class_reg = reg[0]
		class_reg.registration_status = True
		class_reg.save()
		return HttpResponse("Successfully registered.")

	try:
		reg_class = Class.objects.get(pk=class_id)
		school = request.user.userprofile.school
		period = request.user.userprofile.period
		cr = ClassRegistration(
			reg_class=reg_class, student=student, school=school, 
			period=period, registration_status=True)

		cr.save()
		return HttpResponse("Successfully registered.")
	except IntegrityError:
		return HttpResponse("This student is already registered.")
	
	except Exception as e:
		return HttpResponseBadRequest(e)

# delete student from class
@login_required
def class_remove_registration(request, class_id):
	try:
		student_id = request.POST['student_id']
		student = Student.objects.get(pk=student_id)
		reg_class = Class.objects.get(pk=class_id)
		cr = ClassRegistration.objects.filter(
			student=student).filter(reg_class=reg_class)
		cr.delete()
		return HttpResponse("Successfully removed from course.")
	
	except Exception as e:
		return HttpResponseBadRequest(e)

@login_required
def class_attendance(request, class_id=None):
	if request.user.userprofile.role == 'TEACHER':
		teacher_user = TeacherUser.objects.get(user= request.user)
		class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		class_list = []
		for c in class_teacher:
			class_list.append(c.taught_class)
	else:

		class_list = Class.objects.filter(
			school = request.user.userprofile.school, 
			period = request.user.userprofile.period
		).order_by('course')

	context_dictionary = { 'class_list': class_list }

	if class_id:
		c = Class.objects.get(pk=class_id)
		context_dictionary['class'] = c

		class_reg_list = ClassRegistration.objects.filter(reg_class__id = class_id).order_by('student__first_name')
		context_dictionary['classregistration'] = class_reg_list

		AttendanceFormSetFactory = modelformset_factory(ClassAttendance, extra=0, can_delete=True)
		date_form = ClassAttendanceDateForm(initial={'date': datetime.now()})
		context_dictionary['dateform'] = date_form

		if request.method == "POST":

				if '_date' in request.POST:

					date_form = ClassAttendanceDateForm(request.POST)
					inter = date_form['date'].value()
					if '/' in inter:
						x,y,z = inter.split('/')
						date_value = z + "-" + x + "-" + y
					else:
						date_value = inter	

					context_dictionary['date_value'] = date_value

					for cl in class_reg_list:
						verify = ClassAttendance.objects.filter(student=cl.student, reg_class=c, date=date_value)
						if len(verify) == 0:
							ClassAttendance.objects.create(student =cl.student, reg_class=c, date=date_value)

					formset = AttendanceFormSetFactory(queryset=ClassAttendance.objects.filter(date=date_value))
					context_dictionary['formset'] = formset

					date_form = ClassAttendanceDateForm(initial={'date': date_value})
					context_dictionary['dateform'] = date_form

					return render_to_response('classes/class_attendance.html', context_dictionary,
						RequestContext(request))

				elif '_attendance' in request.POST:

					date_form = ClassAttendanceDateForm(request.POST)
					date_value = date_form['date'].value()
					formset = AttendanceFormSetFactory(request.POST, queryset=ClassAttendance.objects.filter(date=date_value))

					if formset.is_valid():

						instances = formset.save(commit=False)
						for instance in instances:
							instance.reg_class = c
							instance.date = date_value
							instance.save()

							context_dictionary['success'] = "Attendance was saved successfully."
						
						create_attendance_notifications(request, c)

					else:
						context_dictionary['errors'] = formset.errors

					context_dictionary['date_value'] = date_value

					formset = AttendanceFormSetFactory(queryset=ClassAttendance.objects.filter(date=date_value))
					context_dictionary['formset'] = formset

					date_form = ClassAttendanceDateForm(initial={'date': date_value})
					context_dictionary['dateform'] = date_form

					return render_to_response('classes/class_attendance.html', context_dictionary,
						RequestContext(request))

		else:
				date_form = ClassAttendanceDateForm()
				inter = date_form['date'].value()
				if inter and '/' in inter:
					x,y,z = inter.split('/')
					date_value = z + "-" + x + "-" + y
				else:
					date_value = inter	
				formset = AttendanceFormSetFactory(queryset=ClassAttendance.objects.filter(date=date_value))
		
		context_dictionary['dateform'] = date_form
		context_dictionary['formset'] = formset

	return render_to_response('classes/class_attendance.html', context_dictionary,
		RequestContext(request))

def create_attendance_notifications(request, class_):
	attendance_notification = NotificationType.objects.get(notification_type='Attendance')
	max_absences = attendance_notification.condition

	#  get all absences in the class
	absences = ClassAttendance.objects.filter(
		reg_class=class_, attendance='A'
	).order_by('student', 'date')

	curr_student = None
	last_absence = 0
	first_absence = 0
	absent_streak = 0

	for absence in absences:

		# if not the same student, check streak and reset
		if curr_student is None or curr_student.id != absence.student.id: 		
			absent_streak = 1
			first_absence = absence.date
			last_absence = absence.date.toordinal()
			curr_student = absence.student

		# if consecutive, increase streak and store date
		elif absence.date.toordinal() - last_absence == 1:
			absent_streak += 1
			last_absence = absence.date.toordinal()

		if absent_streak >= max_absences:
			# check if attendance notification already exists for this student
			# creates another notification only if start of absence is different
			notif_list = Notification.objects.filter(
				notification_type=attendance_notification,
				student=curr_student,
				date=first_absence
				)
			if len(notif_list) == 0:
				notification = Notification(
					notification_type=attendance_notification, 
					student=curr_student,
					school=request.user.userprofile.school,
					period=request.user.userprofile.period,
					date=first_absence,
					status=False)
				notification.save()

		 	



@login_required
def class_performance(request, class_id=None, assignment_id=None):

	if request.user.userprofile.role == 'TEACHER':
		teacher_user = TeacherUser.objects.get(user= request.user)
		class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		class_list = []
		for c in class_teacher:
			class_list.append(c.taught_class)
	else:

		class_list = Class.objects.filter(
			school = request.user.userprofile.school, 
			period = request.user.userprofile.period
		).order_by('course')

	context_dictionary = { 'class_list': class_list }

	if class_id:
		c = Class.objects.get(pk=class_id)
		context_dictionary['class'] = c
		
		class_reg_list = ClassRegistration.objects.filter(reg_class__id = class_id).order_by('student__first_name')
		context_dictionary['classregistration'] = class_reg_list
	
		assigments_list = Assignment.objects.filter(reg_class=c).order_by('-date')
		context_dictionary['assignment_list'] = assigments_list

		if assignment_id:
			a = Assignment.objects.get(pk=assignment_id)
			for cl in class_reg_list:
				verify = Grading.objects.filter(student=cl.student, reg_class=c, assignment=a)
				if len(verify) == 0:
					Grading.objects.create(student =cl.student, reg_class=c, assignment=a)
			context_dictionary['assignment'] = a

			GradingFormSetFactory = inlineformset_factory(Assignment, Grading, extra=0, can_delete=True)
			assignment = Assignment.objects.get(pk=assignment_id)

			if request.method == "POST":

				formset = GradingFormSetFactory(request.POST, instance=assignment)

				if formset.is_valid():

					instances = formset.save(commit=False)
					for instance in instances:
						instance.assignment = a
						instance.reg_class = c
						instance.save()

					#performance
					for cl in class_reg_list:
						current = Grading.objects.get(student=cl.student, reg_class=c, assignment=a)
						grade = current.grade

						if grade == None:
							grade = 0.0
						total = a.total_weight
						current.performance = (grade/total) * 100
						current.save()

					create_performance_notifications(request, c)

				else:
					print('Error')
					context_dictionary['errors'] = formset.errors
					print(formset.errors)

				return HttpResponseRedirect(
						reverse('school:classperformance', args=(class_id, assignment_id)))

			else:
				formset = GradingFormSetFactory(instance=assignment)
				
			context_dictionary['formset'] = formset

	return render_to_response('classes/class_grading.html', context_dictionary,
		RequestContext(request))

def create_performance_notifications(request, c):
	performance_notification = NotificationType.objects.get(notification_type='Performance')
	min_performance = performance_notification.condition

	# go over each student in the class
	students = [x.student for x in c.enrolled_class.all()]
	for student in students:
		per = find_overall_performance(student.id)

		# check if unread notification already exists
		notif_list = Notification.objects.filter(
			notification_type=performance_notification,
			student=student,
			status=False
		)

		#  might return None if no assignments yet
		if per and per < min_performance and len(notif_list) == 0:
			print "Created notification for", student, per
			notif = Notification(
				notification_type = performance_notification,
				student = student,
				school = request.user.userprofile.school, 
				period = request.user.userprofile.period,
				status=False)
			notif.save()

# returns a percent
def find_overall_performance(student_id):
	#  find all the classes this student is registered in
	s = Student.objects.get(pk=student_id)
	classes = [x.reg_class for x in s.enrolled_student.all()]
	grand_total = len(classes) * 100
	class_total = sum(filter(None, 
		[find_class_performance(student_id, c.id) for c in classes]))

	if grand_total == 0:
		return None

	return class_total/grand_total * 100

#  returns a percent
def find_class_performance(student_id, class_id):
	student = Student.objects.get(pk=student_id)
	c = Class.objects.get(pk=class_id)
	performances = Grading.objects.filter(student=student, reg_class=c)
	total_performance = 0 # in percent, weighted by assignment weight

	# for each performance, multiply by each weight 
	for per in performances:
		weight = per.assignment.grade_weight
		total_performance += per.performance * weight

	# at the end divide by total of all assignments for this class
	total_weight = sum(Assignment.objects.filter(
		reg_class=c).values_list('grade_weight', flat=True))

	if (total_weight == 0):
		return None

	return total_performance/total_weight



@login_required
def class_assignment(request, class_id=None):
	
	if request.user.userprofile.role == 'TEACHER':
		teacher_user = TeacherUser.objects.get(user= request.user)
		class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		class_list = []
		for c in class_teacher:
			class_list.append(c.taught_class)
	else:

		class_list = Class.objects.filter(
			school = request.user.userprofile.school, 
			period = request.user.userprofile.period
		).order_by('course')

	context_dictionary = { 'class_list': class_list }

	if class_id:
		c = Class.objects.get(pk=class_id)
		context_dictionary['class'] = c

		assigments_list = Assignment.objects.filter(reg_class=c).order_by('-date')
		context_dictionary['assignments'] = assigments_list
	
	if request.method == 'POST':
		form = ClassAssignmentForm(request.POST, request.FILES)
		if form.is_valid():
			new = form.save(commit=False)
			c = Class.objects.get(pk=class_id)
			new.reg_class = c
			new.content = request.FILES['content']
			new.save()
			# Redirect to the document list after POST
			return HttpResponseRedirect(
				reverse('school:classassignment', args=(class_id,)))
	else:
		form = ClassAssignmentForm()

	context_dictionary['form'] = form


	return render_to_response('classes/class_assignment.html', context_dictionary,
		RequestContext(request))

@login_required
def class_reportcard(request, class_id=None, student_id=None):
	if request.user.userprofile.role == 'TEACHER':
		teacher_user = TeacherUser.objects.get(user= request.user)
		class_teacher = ClassTeacher.objects.filter(teacher=teacher_user)
		class_list = []
		for c in class_teacher:
			class_list.append(c.taught_class)
	else:

		class_list = Class.objects.filter(
			school = request.user.userprofile.school, 
			period = request.user.userprofile.period
		).order_by('course')

	context_dictionary = { 'class_list': class_list }

	if class_id:
		c = Class.objects.get(pk=class_id)
		context_dictionary['class'] = c

	if student_id:
		s = Student.objects.get(pk=student_id)
		context_dictionary['student'] = s

		grading_list = Grading.objects.filter(student=s, reg_class=c).order_by('-assignment__date').reverse()
		context_dictionary['gradinglist'] = grading_list

		cont=0
		for g in grading_list:
			cont = cont + g.performance
		total = len(grading_list)
		if total!= 0:
			average = cont/total
		else:
			average = 0
		# context_dictionary['overall'] = average
		context_dictionary['overall'] = find_class_performance(student_id, c.id)

	return render_to_response('classes/class_reportcard.html', context_dictionary,
		RequestContext(request))
