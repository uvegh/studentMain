from datetime import datetime
# import profile
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.html import escape, mark_safe
from django.core.exceptions import ValidationError

'''

models.py holds database tables and fields for student and supervisors as 
well as their actions

'''


def profile_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'profile_uploads/_{0}/{1}'.format(instance, filename)


class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_supervisor = models.BooleanField(default=False)
    state_of_origin = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    institution = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=30, blank=True)
    profile_pix = models.FileField(upload_to=profile_directory_path, blank=True, null=True)


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,  related_name='student')         
    def __str__(self):
        return self.user.username


class Supervisor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,  related_name='supervisor')         
    def __str__(self):
        return self.user.username


class ProjectMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="sender")
    receiver = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name="receiver")
    message =  models.TextField(max_length=1000, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default = False)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        return f"{self.sender} + {self.receiver}"


class Project(models.Model):
    PROJECT_STATUS = (        
       ("ongoing", "ongoing"),
       ("completed", "completed"),
       ("paused", "paused"),       
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)    
    # detail =  models.TextField(max_length=200, blank=True, null=True)
    status = models.CharField(choices=PROJECT_STATUS, default="ongoing", max_length=255, blank=True, null=True)
    supervisor  =  models.ForeignKey(Supervisor, on_delete=models.DO_NOTHING, blank=True, null=True)
    student  =   models.OneToOneField(Student, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return f'project for {self.supervisor} + {self.student}'

    # def clean(self):
    #     student = Project.objects.filter(status='ongoing').exists()
    #     if student:
    #         raise ValidationError(
    #             {'student': 'student already has to a ongoing'}
    #         )

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'project_uploads/_{0}/{1}'.format(instance.student_id, filename)


class ProjectUplaod(models.Model):
    
    PROJECT_STATUS = (
       ("pending", "pending"),
       ("approved", "approved"),
       ("declined", "declined")
    )

    supervisor = models.ForeignKey(Supervisor, on_delete=models.DO_NOTHING, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, blank=True, null=True)
    title =  models.CharField(max_length=150, null=True)
    detail =  models.TextField(max_length=50000, null=True)
    file = models.FileField(upload_to=user_directory_path, blank=True, null=True, max_length=500)
    file2 = models.FileField(upload_to=user_directory_path, blank=True, null=True, max_length=500)
    project_id  =  models.ForeignKey(Project, on_delete=models.DO_NOTHING,  null=True)
    status = models.CharField(choices=PROJECT_STATUS, default="pending", max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title
    
    # def clean(self):
    #     status = ProjectUplaod.objects.filter(status='pending', project_id=self.project_id)
    #     # print("status", status/)
    #     if status.exists():
    #         raise ValidationError(
    #             {'status': 'student already has a pending upload. wait for approval'}
    #         )
        

class ProjectComment(models.Model):
    project = models.ForeignKey(ProjectUplaod,on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='user')    
    comment = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    # active = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment by {}'.format( self.user)
   

class DefenceCall(models.Model):
    
    CALL_STATUS = (
       ("pending", "pending"),
       ("approved", "approved"),
       ("closed", "closed")
    )

    CALL_TYPE = (
       ("mid_term", "mid_term"),
       ("final", "final"),       
    )

    supervisor = models.ForeignKey(Supervisor, on_delete=models.DO_NOTHING, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, blank=True, null=True)
    detail = models.TextField()
    status = models.CharField(choices=CALL_STATUS, default="pending", max_length=255, blank=True, null=True)
    type = models.CharField(choices=CALL_TYPE, default="final", max_length=255, blank=True, null=True)    
    student_read = models.BooleanField(default=False)
    supervisor_read = models.BooleanField(default=False)
    is_updated = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.student} + {self.supervisor} + {self.type}"


class Meeting(models.Model):

    STATUS = (
        ("active", "active"),
        ("done", "done"),
        ("closed", "closed")
    )

    supervisor = models.ForeignKey(Supervisor, on_delete=models.DO_NOTHING, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, blank=True, null=True)
    title =  models.CharField(max_length=150, null=True)
    detail = models.TextField()      
    datetime =  models.CharField(max_length=250, null=True)  
    status = models.CharField(choices=STATUS, default="active", max_length=255, blank=True, null=True)
    student_read = models.BooleanField(default=False)
    supervisor_read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.student} + {self.supervisor} "


class MeetingComment(models.Model):
    
    STATUS = (
        ("unverified", "unverified"),
        ("verified", "verified"),
    )
    meeting = models.ForeignKey(Meeting,on_delete=models.CASCADE, related_name='meetings')
    user = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='user_meeting_comment')    
    comment = models.TextField()
    verification_status = models.CharField(choices=STATUS, default="unverified", max_length=255, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    # active = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return 'Comment by {}'.format( self.user)
   


class ModelNotifications(models.Model):
    # actor = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='user_meeting_comment')    
    supervisor = models.ForeignKey(Supervisor, on_delete=models.DO_NOTHING, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.DO_NOTHING, blank=True, null=True)    
    notice = models.TextField()
    student_read = models.BooleanField(default=False)
    supervisor_read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.student} + {self.supervisor} "
    
