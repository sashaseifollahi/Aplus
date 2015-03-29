from school_components.models.period_model import Period
from school_components.forms.periods_form import *
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from school_components.utils import *
from django.contrib.auth.decorators import login_required

@login_required
def period_list(request, period_id=None):
	period_list = Period.objects.filter(school = request.user.userprofile.school).order_by('description')
	context_dictionary = {'period_list': period_list}

	if period_id:
                try:
                        c = Period.objects.get(pk=period_id)
                        if request.user.userprofile.role == 'SCHOOL_ADMIN' and c.school != request.user.userprofile.school:
                                raise ObjectDoesNotExist
                        context_dictionary['period'] = c
                except ObjectDoesNotExist:
                        context_dictionary['error'] = 'There is no period with that id.'
                        
	return render_to_response("periods/period_list.html",
		context_dictionary,
		RequestContext(request))

@login_required
def period_create(request):
	period_list = Period.objects.filter(school = request.user.userprofile.school).order_by('description')
	context_dictionary = {'period_list': period_list,
							 'period_form': PeriodForm(), 'period_transfer_form': PeriodTransferForm(cur_school=request.user.userprofile.school,
                                                                                                                          cur_period=request.user.userprofile.period)}
	if request.method == 'POST':
		cf = PeriodForm(request.POST)
		tf = PeriodTransferForm(request.POST, cur_school=request.user.userprofile.school,cur_period=request.user.userprofile.period)

		context_dictionary['period_form'] = cf
		context_dictionary['period_transfer_form'] = tf
		
		if cf.is_valid() and tf.is_valid():
			new = cf.save(commit=False)
			new.school = request.user.userprofile.school
			print (request.user.userprofile.school)
			new.save()
			if tf.fields['transfer_teachers']:
						SchoolUtils.duplicate_teachers(request.user.userprofile.school, request.user.userprofile.period, new)
						selected_courses = tf.courses  
			duplicate_courses(selected_courses, new)

			return HttpResponseRedirect(
				reverse('school:periodlist', args=(new.id,)))
		else:
			context_dictionary['errors'] = cf.errors 

	return render_to_response('periods/period_form.html',
		context_dictionary,
		RequestContext(request))


@login_required
def period_change(request, period_id=None):
	if period_id:
		new_period = Period.objects.get(pk = period_id)
		request.user.userprofile.period = new_period
		request.user.userprofile.save()

	return render_to_response('periods/period_list.html',
		RequestContext(request))

def period_edit(request, period_id): #there should always be a period_id here
    #!!! probably block off this view entirely for anybody but system admin !!!
		period_list = Period.objects.filter(school = request.user.userprofile.school).order_by('description')
		context_dictionary = {'period_list': period_list}

		try:

				c = Period.objects.get(pk=period_id)

                #make sure that school admins can only access by url the periods in their school
				if request.user.userprofile.role == 'SCHOOL_ADMIN' and c.school != request.user.userprofile.school:
					raise ObjectDoesNotExist
                
				context_dictionary['period_id']=period_id
				if request.method == 'POST':
					period_form = PeriodForm(request.POST, instance = c)
					if period_form.is_valid():
						period_form.save()
						context_dictionary['success']=True
				else:
					period_form = PeriodForm(instance = c)
                        
				context_dictionary['period_form'] = period_form

		except ObjectDoesNotExist:
				context_dictionary['error'] = 'There is no period with that id.'

		return render_to_response("periods/period_edit.html",
                        context_dictionary,
                        RequestContext(request))


'''
Delete Period
'''
@login_required
def period_delete(request, period_id):
    Period.objects.get(pk=period_id).delete()
    messages.success(request, "Period has been deleted!")
    return redirect('school:periodlist')
