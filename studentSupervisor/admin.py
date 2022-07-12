from django.contrib import admin

# Register your models here.

from .models import User, Project, ProjectUplaod, Student, Supervisor, \
    ProjectMessage, ProjectComment, DefenceCall, Meeting, ModelNotifications

admin.site.register(User)
admin.site.register(Project)
admin.site.register(ProjectUplaod)
admin.site.register(Student)
admin.site.register(Supervisor)
admin.site.register(ProjectMessage)
admin.site.register(ProjectComment)
admin.site.register(DefenceCall)
admin.site.register(Meeting)
admin.site.register(ModelNotifications)

