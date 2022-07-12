from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.contrib.auth import get_user_model
from ..models import ProjectMessage, ProjectUplaod, Student, Project, Supervisor, ProjectComment, \
    ProjectMessage, User, MeetingComment as MeetingCommentModel, ModelNotifications
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from ..forms import CommentForm, MeetingCommentForm
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.views import View
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.utils.decorators import method_decorator
from ..decorators import supervisor_required


# this class update the read status of a notifcation to true for the actor
# and returns to the same page
@method_decorator([login_required, supervisor_required], name='dispatch')
class ReadTrueSupervisor(UpdateView):
    model = ModelNotifications
    fields = ( )
    template_name = 'supervisors/home.html'

    def form_valid(self, form):

        user = self.request.user        
        # student_id = self.request.POST.get('student_id', '')
        # url = self.request.build_absolute_uri()
        pk = self.kwargs['pk']
        # student = Student.objects.get(user=user)                        
        supervisor = Supervisor.objects.get(user=user)
        form = form.save(commit=False)
        form.supervisor = supervisor  
        form.supervisor_read = True      
        # form.supervisor = supervisor           
        form.save()
        messages.success(self.request, 'Notifcation mark as Read')
        # notice = ModelNotifications.objects.create(student=student, supervisor=supervisor, notice=f"project updated on <a href=\'/project/upload/{pk}\'>view</a>",
        # supervisor_read=True
        # )
        # print('urll', self.request.build_absolute_uri())
        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


# A listView to return lists of students for the logged in supervisor
# its has a 'notice' dictionary to display notifications on the 
# template_name using keyword 'notice'
@method_decorator([login_required, supervisor_required], name='dispatch')
class StudentList(ListView):
     # model = get_user_model()
    paginate_by = 36
    template_name = 'supervisors/home.html'
    context_object_name = 'project_uploads'

    def get_queryset(self):        
        User = get_user_model()
        user = self.request.user        
        supervisor = Supervisor.objects.get(user=user)
        # project_id = Project.objects.filter(supervisor=supervisor)         
        # student = Student.objects.get(user=user)
        # queryset = ProjectUplaod.objects.filter(supervisor=supervisor)
        queryset = Project.objects.filter(supervisor=supervisor)        
        return queryset

    def get_context_data(self,**kwargs):
        context = super(StudentList,self).get_context_data(**kwargs)
        user = self.request.user   
        supervisor = Supervisor.objects.get(user=user)
        notice = None
        supervisor_read = False
        notice = ModelNotifications.objects.filter(supervisor=supervisor, supervisor_read=supervisor_read)
        context['notice'] = notice                         
        return context  
 

# displays list of all students uploads for the logged in supervisor
# the specific student is gotten by using kwags['student_id'] which is the student id
@method_decorator([login_required, supervisor_required], name='dispatch')
class StudentProjectUpload(ListView):
     # model = get_user_model()
    paginate_by = 36
    template_name = 'supervisors/upload_list.html'
    context_object_name = 'project_uploads'

    def get_queryset(self):        
        User = get_user_model()
        user = self.request.user        
        supervisor = Supervisor.objects.get(user=user)
        # project_id = Project.objects.filter(supervisor=supervisor)         
        # student = Student.objects.get(user=user)
        # queryset = ProjectUplaod.objects.filter(supervisor=supervisor)
        queryset = Project.objects.filter(supervisor=supervisor)        
        return queryset

    def get_context_data(self,**kwargs):
        context = super(StudentProjectUpload,self).get_context_data(**kwargs)
        user = self.request.user          
        supervisor = Supervisor.objects.get(user=user)   
        query = self.kwargs['student_id']
        student_name = Student.objects.get(user=query)
        context['student_name'] = student_name         
        context['student'] = query 
        context['object_list'] = ProjectUplaod.objects.filter(supervisor=supervisor, student=self.kwargs['student_id'])       
        return context  



# Supervisor updates proejct status by firing this view through the url
# and the student is notified by creating a notification for the student
@method_decorator([login_required, supervisor_required], name='dispatch')
class ProjectUpdate(UpdateView):
    model = ProjectUplaod
    fields = ('status',  )
    template_name = 'supervisors/project_upload_datail.html'

    def form_valid(self, form):

        student_id = self.request.POST.get('student_id', '')
        # url = self.request.build_absolute_uri()
        pk = self.kwargs['pk']
        student = Student.objects.get(user=student_id)                
        user = self.request.user        
        supervisor = Supervisor.objects.get(user=user)
        form = form.save(commit=False)
        form.student = student        
        form.supervisor = supervisor           
        form.save()
        messages.success(self.request, 'Project status was updated successfully')
        notice = ModelNotifications.objects.create(student=student, supervisor=supervisor, notice=f"project status updated. <a href=\'/project/upload/{pk}\'>view</a>",
        supervisor_read=True
        )
        # print('urll', self.request.build_absolute_uri())
        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))



# this view shows the content of a specific project upload
# as well as the comment form and displays comment/reviews made
# by both parties
@method_decorator([login_required, supervisor_required], name='dispatch')
class StudentProjectUploadDetailView(DetailView):
    model = ProjectUplaod
    template_name = 'supervisors/project_upload_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(StudentProjectUploadDetailView, self).get_context_data(*args, **kwargs)        
        user = self.request.user  
        if user.is_superuser:
            project = Project.objects.all()
        else:
            # student = Student.objects.get(user=user)   
            # project_id = Project.objects.get(student=student)
            project = ProjectUplaod.objects.filter(pk=self.kwargs['pk'])
            # print(project)
            # project = None

        # try:
        #     # project = Project.objects.get(student_id=student)
        #     # supervisor = project.supervisor_id
        #     # print("supervsss", supervisor)
        # except:
        #     pass
        context["project"] = project
        context['form'] = CommentForm()
        context['comments'] = ProjectComment.objects.filter(project=self.get_object())
        return context    


# this view takes the post request on the upload detail page to
# to post comment and validates it, save it, get the success url on
# and return user back to the project it belongs to
@method_decorator([login_required, supervisor_required], name='dispatch')
class PostComment(SingleObjectMixin, FormView):
    model = ProjectUplaod
    form_class = CommentForm
    template_name = 'supervisors/project_upload_detail.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(PostComment, self).get_form_kwargs()
        # kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.project = self.object
        comment.user = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        post = self.get_object()   
        pk = post.pk
        student = post.student
        supervisor = post.supervisor
        # print("student", student)
        messages.success(self.request, 'Project comment posted successfully')
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor, notice=f"project comment from supervisor on <a href=\'/project/upload/{pk}\'>view</a>",
        supervisor_read=True)     
        return reverse('project_upload_detail_supervisor', kwargs={'pk': post.pk})



# this view handles the request for get, thats to view a project upload content or
# or post request, thats to post a comment/review on a project accordingly
# each request type fires its view
@method_decorator([login_required, supervisor_required], name='dispatch')
class PostDetailView(View):

    def get(self, request, *args, **kwargs):
        view = StudentProjectUploadDetailView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = PostComment.as_view()
        return view(request, *args, **kwargs)



# list all messages for both parties 
# the specific student is gotten from the url query params
@method_decorator([login_required, supervisor_required], name='dispatch')
class ViewMessages(ListView):
    template_name = 'supervisors/view_message.html'
    context_object_name = 'messages'

    def get_queryset(self):
        query = self.request.GET.get('user_id','')
        User = get_user_model()
        user = self.request.user             
        # queryset = None
        # if query:
            # queryset = queryset.annotate(
            #     full_name = Concat('first_name','last_name')
            # ).filter(full_name__icontains = query)
        queryset = ProjectMessage.objects.filter(Q(sender=user, receiver=self.kwargs['student_id']) | Q(sender=self.kwargs['student_id'], receiver=user) )         

    def get_context_data(self,**kwargs):
        context = super(ViewMessages,self).get_context_data(**kwargs)
        user = self.request.user             
        query = self.kwargs['student_id']
        context['student'] = query 
        context['object_list'] = ProjectMessage.objects.filter(Q(sender=user, receiver=self.kwargs['student_id']) | Q(sender=self.kwargs['student_id'], receiver=user) )         
        return context



# this view handles the get request to view list of messages or
# post request to send a message and sends notification on succcess
# and redirects to same page
@method_decorator([login_required, supervisor_required], name='dispatch')
class SupervisorMessageStudent(View):
    template_name = 'supervisors/veiw_message.html'

    def get(self, request, *args, **kwargs):
       return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):        
        query = self.request.POST.get('student_id','')
        user =  self.request.user
        supervisor = Supervisor.objects.get(user=user)
        student_notice = Student.objects.get(user_id=query)
        # student = Student.objects.get(user=user)   
        # project = Project.objects.get(student_id=student)
        # supervisor = project.supervisor.user        
        # receiver_id = Project.objects.get(supervisor=supervisor)
        message = request.POST.get('message', '')
        receiver = request.POST.get('student_id', '')
        student  = User.objects.get(id=receiver)
        ProjectMessage.objects.create(sender=request.user, receiver=student, message=message)
        notice = ModelNotifications.objects.create(student=student_notice, 
        supervisor=supervisor, notice=f"Message from supervisor  <a href=\'message/list/\'>view</a>",
        supervisor_read=True) 

        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))



from ..models import DefenceCall, Meeting


#updates student defence request and send notification to the specific student
# supervisor_read is set to true, student will see the status and
# supervisor read status
@method_decorator([login_required, supervisor_required], name='dispatch')
class StudentDefenceCall(UpdateView):
    model = DefenceCall
    fields = ('status',  )
    template_name = 'supervisors/defence_call.html'

    def form_valid(self, form):

        student_id = self.request.POST.get('student_id', '')
        student = Student.objects.get(user=student_id)                
        user = self.request.user        
        supervisor = Supervisor.objects.get(user=user)
        form = form.save(commit=False)
        form.student = student        
        form.supervisor = supervisor 
        form.supervisor_read = True      
        form.save()
        messages.success(self.request, 'The defence rquest status was updated successfully')
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor, notice=f"Defence call request was reviewed by your supervisor  <a href=\'defence/call/\'>view</a>",
        supervisor_read=True) 
        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))



#list of student defence request for a specfic student gotten
# using student_id from the url
@method_decorator([login_required, supervisor_required], name='dispatch')
class StudentDefenceCallView(ListView):
    template_name = 'supervisors/defence_call.html'
    # context_object_name = 'messages'

    def get_queryset(self):        
        User = get_user_model()
        # user = self.request.user     
        # student = Student.objects.get(user=user)   
        # project = Project.objects.get(student_id=student)
        # project = Project.objects.get(student_id=student)
        # supervisor = project.supervisor_id          
        # queryset = DefenceCall.objects.filter(student=student) 
        # return queryset

    def get_context_data(self,**kwargs):
        context = super(StudentDefenceCallView,self).get_context_data(**kwargs)
        user = self.request.user          
        supervisor = Supervisor.objects.get(user=user)   
        query = self.kwargs['student_id']
        context['student'] = query 
        context['object_list'] = DefenceCall.objects.filter(supervisor=supervisor, student=self.kwargs['student_id'])       
        return context



# supervisor meeting list associated with a specific student
#  using student_id gotten from the url
# the object list is using on the html template
@method_decorator([login_required, supervisor_required], name='dispatch')
class SupervisorMeetingList(ListView):
    template_name = 'supervisors/meeting_list.html'
    # context_object_name = 'messages'

    def get_queryset(self):        
        User = get_user_model()
        # user = self.request.user     
        # student = Student.objects.get(user=user)   
        # project = Project.objects.get(student_id=student)
        # project = Project.objects.get(student_id=student)
        # supervisor = project.supervisor_id          
        # queryset = DefenceCall.objects.filter(student=student) 
        # return queryset

    def get_context_data(self,**kwargs):
        context = super(SupervisorMeetingList,self).get_context_data(**kwargs)
        user = self.request.user          
        supervisor = Supervisor.objects.get(user=user)   
        query = self.kwargs['student_id']
        context['student'] = query 
        context['object_list'] = Meeting.objects.filter(supervisor=supervisor, student=self.kwargs['student_id'])       
        return context



#  meeting detail view
# displays detailed content of a specific meeting between the two parties
# as well as the update form for supervisor to verify a comment/minute/review
# made by a student through the 'form' keyword
# as well as displays the comment form
@method_decorator([login_required, supervisor_required], name='dispatch')
class MeetingDetail(DetailView):
    model = Meeting
    template_name = 'supervisors/meeting_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(MeetingDetail, self).get_context_data(*args, **kwargs)        
        user = self.request.user  
        if user.is_superuser:
            project = Project.objects.all()
        else:
            # student = Student.objects.get(user=user)   
            # project_id = Project.objects.get(student=student)
            project = ProjectUplaod.objects.filter(pk=self.kwargs['pk'])
            print(project)
            # project = None

        # try:
        #     # project = Project.objects.get(student_id=student)
        #     # supervisor = project.supervisor_id
        #     # print("supervsss", supervisor)
        # except:
        #     pass
        context["project"] = project
        context['form'] = MeetingCommentForm()
        context['comments'] = MeetingCommentModel.objects.filter(meeting=self.get_object())
        return context    


# this process a post request to update a comment made on a meeting verified status
@method_decorator([login_required, supervisor_required], name='dispatch')
class MeetingComment(SingleObjectMixin, FormView):
    model = Meeting
    form_class = MeetingCommentForm
    template_name = 'supervisors/meeting_detail.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(MeetingComment, self).get_form_kwargs()
        # kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.project = self.object
        comment.user = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        post = self.get_object()
        # pk = post.pk
        # student = post.student
        # supervisor = post.supervisor
        # notice = ModelNotifications.objects.create(student=student, 
        # supervisor=supervisor, notice=f"Meeting schedule was reviewd <a href=\'/meeting/{pk}\'>view</a>",
        # supervisor_read=True) 
        messages.success(self.request, 'Meeting comment status updated successfully')
        return reverse('meeting_detail_supervisor', kwargs={'pk': post.pk})



# this handles post or get request made to a specific meeting
@method_decorator([login_required, supervisor_required], name='dispatch')
class SupervisorMeetingDetailView(View):

    def get(self, request, *args, **kwargs):
        view = MeetingDetail.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = MeetingComment.as_view()
        return view(request, *args, **kwargs)



# view for supervisor to update meeting status
@method_decorator([login_required, supervisor_required], name='dispatch')
class SupervisorMeetingUpdate(UpdateView):
    model = MeetingCommentModel
    fields = ('verification_status',  )
    template_name = 'supervisors/defence_call.html'

    def form_valid(self, form):

        # student_id = self.request.POST.get('student_id', '')
        # student = Student.objects.get(user=student_id)                
        user = self.request.user        
        supervisor = Supervisor.objects.get(user=user)
        form = form.save(commit=False)
        # form.student = student        
        form.user = user 
        # form.verification_status = True      
        form.save()
        messages.success(self.request, 'Meeting review was updated successfully!')

             
        pk = self.kwargs['pk']          
        user_ = MeetingCommentModel.objects.get(pk=pk)        
        user_1 = user_.meeting
        # print('kwwwwaaarg', user_1.student)
        user_2 = user_1.student
        meeting_id = user_1.id
        
        notice = ModelNotifications.objects.create(student=user_2, 
        supervisor=supervisor, notice=f"Meeting comment made by you was reviewd <a href=\'/meeting/{meeting_id}\'>view</a>",
        supervisor_read=True) 

        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

from ..forms import SupervisorSignUpForm
from django.contrib.auth import login


class SupervisorSignUpView(CreateView):
    model = User
    form_class = SupervisorSignUpForm
    template_name = 'registration/supervisor_signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'supervisor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')