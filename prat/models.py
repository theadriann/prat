from datetime import date
import datetime
from django.contrib.auth.models import User
from django.db import models


# More


class UserProfile(models.Model):
    """model class for a user profile, 1-to-1 relationship with User model,
       stores additional information about a user (timezone, language,
       display name, etc)
    """

    # Properties
    first_name = models.CharField(max_length = 100, blank = True, null = True)
    last_name  = models.CharField(max_length = 100, blank = True, null = True)
    birthday   = models.DateField(null = True, blank = True)
    gender = models.CharField(max_length = 1,
        choices = (
            ('M', 'Male'),
            ('F', 'Female')
        ), blank = True, null = True)
    avatar = models.ImageField(upload_to = 'images/avatars/',
        default = 'images/avatars/no_avatar.jpg', blank = True, null = True)
    points = models.IntegerField(default = 0, null = False)
    experience = models.IntegerField(default = 0, null = False)
    level = models.IntegerField(default = 1, null = False)

    # Relations
    user = models.OneToOneField(User, on_delete = models.CASCADE,
                    related_name = 'profile', verbose_name = 'user')

    def __unicode__(self):
        return u'{} - {}'.format(self.user.username, self.first_name, self.last_name)

    def giveExperience(self, exp):
        self.experience = self.experience + exp
        self.save()
        self.checkLevel()

    def checkLevel(self):
        expNeeded = self.expNeeded()
        if(self.experience >= expNeeded):
            self.experience = self.experience - expNeeded
            self.level = self.level + 1
            self.save()

    def expNeeded(self):
        expNeeded = 100
        for x in range(self.level - 1):
            expNeeded *= 2
        return expNeeded


class Task(models.Model):
    """model class for a task, M-to-1 relationship with UserProfile model,
       1-to-1 with UserGroup model, 1-to-M with UserTaskActivity model,
       M-to-1 with Category model, M-to-1 with UserTaskEvidence model,
       a task is set and completed by a user
    """

    # Properties
    name = models.CharField(max_length = 100, null = False)
    sessions_record = models.IntegerField(default = 0, null = False)
    sessions_total = models.IntegerField(default = 0, null = False)
    experience_total = models.IntegerField(default = 0, null = False)
    experience_reward = models.IntegerField(default = 10, null = False)
    experience_sessions = models.IntegerField(default = 1, null = False)
    experience_multiplier = models.FloatField(default = .02, null = False)
    points_total = models.IntegerField(default = 0, null = False)
    points_reward = models.IntegerField(default = 1, null = False)
    points_sessions = models.IntegerField(default = 1, null = False)
    points_multiplier = models.FloatField(default = 0.01, null = False)
    last_update = models.DateTimeField(auto_now_add = True, null = False)
    # more to come

    # Relations
    category = models.ForeignKey('Category', verbose_name = 'category',
                    related_name = 'tasks', on_delete = models.CASCADE)
    owner = models.ForeignKey(User, verbose_name = 'owner',
                    related_name = 'tasks', on_delete = models.CASCADE)
    ong = models.ForeignKey('Ong', verbose_name = 'ong', related_name = 'tasks',
                    null = True, on_delete = models.SET_NULL)
    theme = models.ForeignKey('Theme', verbose_name = 'theme', null = True)

    def __unicode__(self):
        return u'{} - {}'.format(self.name, self.owner.username)

    def completed(self):
        task_activities = UserTaskActivity.objects.filter(task = self, date_created__gte = date.today())
        # dates = map(lambda x: x.date_created, task_activities)
        # dates = map(lambda x: True if (date.today() - x.date()).days == 0 else False, dates)
        return True if task_activities.count() > 0 else False

    def overdue(self):
        task_activities = UserTaskActivity.objects.filter(task = self)
        if task_activities.count() == 0:
            return False

        last_activity = task_activities.reverse()[0]
        if (date.today() - last_activity.date_created.date()).days >= 2:
            return True
        return False

    def activity_length(self):
        if self.overdue():
            print "[Task-ActivityLength] Overdue!"
            return 0

        task_activities = UserTaskActivity.objects.filter(task = self)
        if task_activities.count() == 0:
            print "[Task-ActivityLength] 0 Activity!"
            return 0

        last_date = date.today()
        streak = 0
        last_activities = task_activities.reverse()

        for activity in last_activities:
            if (last_date - activity.date_created.date()).days >= 2:
                return streak
            else:
                last_date = activity.date_created.date()
                streak = streak + 1
        return streak

    def chain(self):
        today = date.today()
        chain = []
        for i in range(0, 31):
            day = today - datetime.timedelta(days=i)
            activity = UserTaskActivity.objects.filter(task = self, date_created__contains = day).first()
            if activity is None:
                activity = {
                    'date': day
                }

            chain.append(activity)
        return chain


class PredefinedTask(models.Model):
    """model class for predefined tasks, M-to-1 relationship with Category model,
       a set of predefined tasks (ex: workout, floss, take vitamins)
    """

    # Properties
    # later

    # Relations
    category = models.ForeignKey('Category', verbose_name = 'category',
                    related_name = 'predef_tasks', on_delete = models.CASCADE)


class UserGroup(models.Model):
    """model class for a group of users, M-to-M relationship with UserProfile
       model, 1-to-M with Comment model,
       a group of users shares a task
    """

    # Properties
    name = models.CharField(max_length = 100, null=False)
    description = models.CharField(max_length=500, default="")

    # Relations
    members = models.ManyToManyField(User, through='UserGroupMembership')


    def members_num(self):
        members = UserGroupMembership.objects.filter(group=self.pk)
        return len(members)

    def members_arr(self):
        memberships = UserGroupMembership.objects.filter(group=self.pk)
        members = []
        for membership in memberships:
            members.append(membership.user)
        return members

    def __unicode__(self):
        return self.name


class UserGroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_group_task = models.ForeignKey(Task, null=True)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    date_joined = models.DateField()

    class Meta:
        unique_together = (('user', 'user_group_task', 'group'))


class UserGroupComment(models.Model):
    """model class for a comment on a group chat, M-to-1 relationship with
       UserGroup model, M-to-1 with User
       each group has multiple comments
    """

    # Properties
    text = models.CharField(max_length = 200)
    date_added = models.DateTimeField(auto_now_add = True)


    # Relations
    group = models.ForeignKey('UserGroup', related_name = 'comments',
                    verbose_name = 'group', on_delete = models.CASCADE)
    user  = models.ForeignKey(User, related_name = 'comments',
                    verbose_name = 'user', on_delete = models.CASCADE)

    def __unicode__(self):
        return u'{} @ {}'.format(self.user.username, self.text)


class Theme(models.Model):
    """model class for a theme, 1-to-M relationship with UserThemes model,
       a theme is a set of preferences (ex: chain appearance, colours, etc)
    """

    # Properties
    name = models.CharField(max_length = 100)
    price = models.IntegerField(default = 0, null = False)
    description = models.CharField(max_length = 500, blank = True, null = True)
    class_name = models.CharField(max_length = 100, default = 'default', null = False)
    image = models.ImageField(upload_to = 'images/themes/',
        default = 'images/theme/no_theme.jpg', blank = True, null = True)

    def __unicode__(self):
        return u'{} @ {}'.format(self.name, self.class_name)


class UserThemes(models.Model):
    """model class for user-themes, M-to-1 relationship with Theme model,
       M-to-1 with user,
       associative entity, each user has multiples themes he can pick
    """

    # Relations
    theme = models.ForeignKey(Theme, on_delete = models.CASCADE)
    user = models.ForeignKey(User, on_delete = models.CASCADE)

    def __unicode__(self):
        return u'{} @ {}'.format(self.user.username, self.theme.name)


class Achievement(models.Model):
    """model class for an achievement, M-to-M relationship with UserProfile model,
       an achievement is earned by a user (ex: )
    """

    name = models.CharField(max_length = 100)


class Category(models.Model):
    """model class for a category, 1-to-M relationship with PredefinedTask model,
       1-to-M with Task model,
       a classification of tasks (ex: health, study, etc)
    """

    name = models.CharField(max_length = 100)

    def __unicode__(self):
        return u'{}'.format(self.name)


class UserTaskActivity(models.Model):
    """model class for a user-task activity, M-to-1 relationship with Task model,
       tracks daily progress for a user's task
    """

    # Properties
    date_created = models.DateTimeField(auto_now_add = True, null = False, editable = True)
    experience_gained = models.IntegerField(default = 0, null = False)
    points_gained = models.IntegerField(default = 0, null = False)

    # Relations
    task = models.ForeignKey('Task', verbose_name = 'task',
                    on_delete = models.CASCADE)
    user = models.ForeignKey(User, verbose_name = 'user',
                    on_delete = models.CASCADE)

    def __unicode__(self):
        return u'{} - {} - {}'.format(self.user.username, self.task.name, self.date_created.date())


class Ong(models.Model):
    """ Ongs to which donations, from points achieved by users, will go"""

    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    image = models.ImageField(upload_to = 'images/ongs/', blank = True, null = True)

    def tasks_num(self):
        tasks = Task.objects.filter(ong = self.pk)
        return len(tasks)

    def __unicode__(self):
        return u'{}'.format(self.name)
