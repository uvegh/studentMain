from django import views
from django.shortcuts import render, get_object_or_404, redirect, render
from django.contrib.auth import get_user_model
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from ..models import Project, ProjectUplaod, Student, ProjectMessage, ProjectComment, Supervisor, ModelNotifications
from django.views import View
from django.contrib import messages
from django.db.models import Q
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse
from ..forms import CommentForm, MeetingComment, MeetingCommentForm


# Create your views here.
# this file 'views.py' handles
# requests from clients through urls
# and returns reponses

from ..models import User
from ..forms import StudentSignUpForm
from django.contrib.auth import login


# sign view view for students
# any user who sign up through this view is automatically a student
class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')


# this class update the read status of a notifcation to true for the student
# and returns to the same page
class ReadTrue(UpdateView):
    model = ModelNotifications
    fields = ( )
    template_name = 'student/home.html'

    def form_valid(self, form):

        user = self.request.user        
        # student_id = self.request.POST.get('student_id', '')
        # url = self.request.build_absolute_uri()
        pk = self.kwargs['pk']
        student = Student.objects.get(user=user)                        
        # supervisor = Supervisor.objects.get(user=user)
        form = form.save(commit=False)
        form.student = student  
        form.student_read = True      
        # form.supervisor = supervisor           
        form.save()
        messages.success(self.request, 'Notification mark as read successfully')
        # notice = ModelNotifications.objects.create(student=student, supervisor=supervisor, notice=f"project updated on <a href=\'/project/upload/{pk}\'>view</a>",
        # supervisor_read=True
        # )
        # print('urll', self.request.build_absolute_uri())
        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


# view for student to upload project contents,
# as well as notify the supervisor
class StudentProjectUpload(CreateView):
    model = ProjectUplaod
    fields = ('title', 'detail', 'file', 'file2' )
    template_name = 'students/project_upload.html'

    def form_valid(self, form):
        user = self.request.user
        student = Student.objects.get(user=user) 
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor_id
        supervisor = Supervisor.objects.get(user=supervisor)
        project_id = Project.objects.get(student=student)        
        quiz = form.save(commit=False)
        quiz.project_id = project_id
        quiz.student = student
        quiz.supervisor = supervisor
        # quiz.status = form.HiddenInput()
        status = ProjectUplaod.objects.filter(status='pending', project_id=project_id)
        if status.exists():
            messages.error(self.request, 'Your project uplaod failed! Pending project upload exists.')
            return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))
        else:
            quiz.save()
            messages.success(self.request, 'The project uplaod was created successfully.')
            notice = ModelNotifications.objects.create(student=student, 
            supervisor=supervisor, notice=f"Project was uploaded by <b>{student}</b> ",
            supervisor_read=False, student_read=True) 
            return redirect('home')


# view for displaying informations about curently logged in user
# project, profile and project status
class StudentProject(View):
    template_name = 'students/home.html'

    def get(self, request, *args, **kwargs):            
        user = request.user  
        project = None
        if  request.user.is_anonymous:
            return redirect('login')
        if user.is_supervisor:
            return redirect('supervisor_home')
        if user.is_superuser:
            project = Project.objects.all()
        else:
            student = Student.objects.get(user=user)   
            try:
                project_id = Project.objects.get(student=student)
                uploads = ProjectUplaod.objects.filter(project_id=project_id)
                project = None
            except:
                pass                

        try:
            project = Project.objects.get(student_id=student)
            supervisor = project.supervisor_id
            notice = None
            student_read = False
            notice = ModelNotifications.objects.filter(student=student, supervisor=supervisor, student_read=student_read)
            # print("notice", notice)
        except:
            pass
        
        if not project:            
            return render(request, self.template_name, {'project': "NO PROJECT ALLOCATED YET"})        
        return render(request, self.template_name, {'project': project, 'project_uploads': uploads, 'notice':notice})


# lits of projects contents uploaded by the logged in student
class ProjectUploadsListView(ListView):
     # model = get_user_model()
    paginate_by = 36
    template_name = 'students/home.html'
    context_object_name = 'project_uploads'

    def get_queryset(self):        
        User = get_user_model()
        user = self.request.user
        student = Student.objects.get(user=user)
        project_id = Project.objects.get(Student=student)
        queryset = None     
        queryset = ProjectUplaod.objects.filter(id=project_id)
        return queryset



# detailed view of a specific project, gotten by the project upload id
# as well as display comment form and list of comments attached to the
# project upload
class ProjectUploadsDetailView(DetailView):
    model = ProjectUplaod
    template_name = 'students/project_upload_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(ProjectUploadsDetailView, self).get_context_data(*args, **kwargs)        
        user = self.request.user  
        if user.is_superuser:
            project = Project.objects.all()
        else:
            student = Student.objects.get(user=user)   
            project_id = Project.objects.get(student=student)
            uploads = ProjectUplaod.objects.filter(project_id=project_id)
            project = None

        try:
            project = Project.objects.get(student_id=student)
            # supervisor = project.supervisor_id
            # print("supervsss", supervisor)
        except:
            pass
        context["project"] = project
        context['form'] = CommentForm()
        context['comments'] = ProjectComment.objects.filter(project=self.get_object())
        return context    


# view that process a post request to submit a comment or review
# on a specific project upload and notifies the suprvisor on sucess submit
class PostComment(SingleObjectMixin, FormView):
    model = ProjectUplaod
    form_class = CommentForm
    template_name = 'students/project_upload_detail.html'

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
        messages.success(self.request, 'Comment posted successfully!')
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor, notice=f"project comment from {student} on <a href=\'/supervisor/project/upload/{pk}\'>view</a>",
        supervisor_read=False, student_read=True)     
        return reverse('project_upload_detail', kwargs={'pk': post.pk})


# this view handles the request for get, thats to view a project upload content or
# or post request, that's to post a comment/review on a project.
# each request type fires its view
class PostDetailView(View):

    def get(self, request, *args, **kwargs):
        view = ProjectUploadsDetailView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = PostComment.as_view()
        return view(request, *args, **kwargs)


# list all messages for both parties 
class ViewMessages(ListView):
    template_name = 'students/view_message.html'
    context_object_name = 'messages'

    def get_queryset(self):
        # query = self.request.GET.get('q','')
        User = get_user_model()
        user = self.request.user     
        student = Student.objects.get(user=user)   
        project = Project.objects.get(student_id=student)
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor_id  
        # queryset = None
        # if query:
            # queryset = queryset.annotate(
            #     full_name = Concat('first_name','last_name')
            # ).filter(full_name__icontains = query)
        queryset = ProjectMessage.objects.filter(Q(sender=user) | Q(receiver=user) ) 
        return queryset


# this view handles the get request to view list of messages or
# post request to send a message and sends notification on succcess
# and redirects to same page
class StudentMessageSupervisor(View):
    template_name = 'students/veiw_message.html'

    def get(self, request, *args, **kwargs):
       return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):
        user = request.user  
        student = Student.objects.get(user=user)   
        student_id = Student.objects.get(user_id=user)
        student_id = student_id.user_id
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor.user        
        supervisor_ = Supervisor.objects.get(user=supervisor)
        # receiver_id = Project.objects.get(supervisor=supervisor)
        message = request.POST.get('message', '')
        ProjectMessage.objects.create(sender=request.user, receiver=supervisor, message=message)
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor_, notice=f"Message from {student}  <a href=\'message/list/student_id={student_id}/\'>view</a>",
        supervisor_read=False, student_read=True) 
        return redirect('view_messages')


from ..models import DefenceCall, Meeting


#student request for defence view
# sends notification to supervisor on success
class StudentDefenceCall(CreateView):
    model = DefenceCall
    fields = ('type', 'detail' )
    template_name = 'students/defence_call.html'

    def form_valid(self, form):
        user = self.request.user
        student = Student.objects.get(user=user)         
        student_id = Student.objects.get(user_id=user)
        student_id = student_id.user_id
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor 
        form = form.save(commit=False)
        form.student = student        
        form.supervisor = supervisor 
        form.student_read = True      
        form.save()
        messages.success(self.request, 'Defence request sent successfully!')
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor, notice=f"A Defence schedule was requested by {student} <a href=\'defence/call/student_id={student_id}/\'>view</a>",
        supervisor_read=False, student_read=True) 
        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))



#student request for defence list
class StudentDefenceCallView(ListView):
    template_name = 'students/defence_call.html'
    # context_object_name = 'messages'

    def get_queryset(self):        
        User = get_user_model()
        user = self.request.user     
        student = Student.objects.get(user=user)   
        project = Project.objects.get(student_id=student)
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor_id          
        queryset = DefenceCall.objects.filter(student=student) 
        return queryset


# student meeting setup view
class StudentMeetingCreate(CreateView):
    model = Meeting
    fields = ('title', 'detail', 'datetime' )
    template_name = 'students/meeting.html'

    def form_valid(self, form):
        user = self.request.user
        student = Student.objects.get(user=user)         
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor 
        form = form.save(commit=False)
        form.student = student        
        student_id = Student.objects.get(user_id=user)
        student_id = student_id.user_id
        form.supervisor = supervisor 
        form.student_read = True      
        form.save()
        messages.success(self.request, 'The Meeting schedule was created successfully!')
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor, notice=f"A Meeting schedule was set up by {student} <a href=\'meeting/list/student_id={student_id}/\'>view</a>",
        supervisor_read=False, student_read=True) 
        return redirect(self.request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))


#student meeting list view
class StudentMeetingList(ListView):
    template_name = 'students/meeting.html'
    # context_object_name = 'messages'

    def get_queryset(self):        
        User = get_user_model()
        user = self.request.user     
        student = Student.objects.get(user=user)   
        project = Project.objects.get(student_id=student)
        project = Project.objects.get(student_id=student)
        supervisor = project.supervisor_id          
        queryset = Meeting.objects.filter(student=student) 
        return queryset


# view for specific detailed view of meeting to show its full content
# as well as display comment form and lists of comment made on the meeting
class MeetingDetail(DetailView):
    model = Meeting
    template_name = 'students/meeting_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super(MeetingDetail, self).get_context_data(*args, **kwargs)        
        user = self.request.user  
        if user.is_superuser:
            Meeting = Project.objects.all()
        else:
            student = Student.objects.get(user=user)   
            project_id = Project.objects.get(student=student)
            uploads = ProjectUplaod.objects.filter(project_id=project_id)
            Meeting = None

        try:
            Meeting = Project.objects.get(student_id=student)
            # supervisor = project.supervisor_id
            # print("supervsss", supervisor)
        except:
            pass
        context["project"] = Meeting
        context['form'] = MeetingCommentForm()
        context['comments'] = MeetingComment.objects.filter(meeting=self.get_object())
        return context    



# this process a post request to create a comment made on a meeting
# send notification to student
class PostMeetingComment(SingleObjectMixin, FormView):
    model = Meeting
    form_class = MeetingCommentForm
    template_name = 'students/meeting_detail.html'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(PostMeetingComment, self).get_form_kwargs()
        # kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.meeting = self.object
        comment.user = self.request.user
        comment.save()
        return super().form_valid(form)

    def get_success_url(self):
        post = self.get_object()
        pk = post.pk
        student = post.student
        supervisor = post.supervisor        
        notice = ModelNotifications.objects.create(student=student, 
        supervisor=supervisor, notice=f"A meeting comment from {student}  <a href=\'meeting/{pk}\'>view</a>",
        supervisor_read=False, student_read=True) 
        return reverse('meeting_detail', kwargs={'pk': post.pk})



# this handles post or get request made to a specific meeting
class MeetingDetailView(View):

    def get(self, request, *args, **kwargs):
        view = MeetingDetail.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = PostMeetingComment.as_view()
        return view(request, *args, **kwargs)







