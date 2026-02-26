from django.db import models
from django.conf import settings


class Trend(models.Model):
    CATEGORY_CHOICES = [
        ('entertainment', 'Entertainment'),
        ('technology', 'Technology'),
        ('sports', 'Sports'),
        ('politics', 'Politics'),
        ('fashion', 'Fashion'),
        ('music', 'Music'),
        ('gaming', 'Gaming'),
        ('food', 'Food & Lifestyle'),
        ('business', 'Business'),
        ('science', 'Science'),
        ('other', 'Other'),
    ]

    PLATFORM_CHOICES = [
        ('twitter', 'Twitter/X'),
        ('tiktok', 'TikTok'),
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube'),
        ('reddit', 'Reddit'),
        ('linkedin', 'LinkedIn'),
        ('threads', 'Threads'),
    ]

    VELOCITY_CHOICES = [
        ('exploding', 'Exploding'),
        ('rising', 'Rising'),
        ('steady', 'Steady'),
        ('declining', 'Declining'),
    ]

    SOURCE_CHOICES = [
        ('manual', 'Manual'),
        ('google_trends', 'Google Trends'),
        ('news', 'News'),
        ('stocks', 'Stocks'),
        ('youtube', 'YouTube'),
        ('music', 'Music'),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    description = models.TextField()
    score = models.FloatField(default=0.0, db_index=True)
    velocity = models.CharField(max_length=20, choices=VELOCITY_CHOICES, default='rising')
    embed_url = models.URLField(blank=True, null=True)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES, default='manual', db_index=True)
    external_url = models.URLField(blank=True, null=True)
    source_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-score', '-created_at']
        indexes = [
            models.Index(fields=['category', 'score']),
            models.Index(fields=['created_at', 'score']),
        ]

    def __str__(self):
        return self.title

    @property
    def total_engagement(self):
        return self.likes + self.shares + self.comments

    @property
    def velocity_color(self):
        colors = {
            'exploding': '#ff4444',
            'rising': '#ff8800',
            'steady': '#00aa44',
            'declining': '#888888',
        }
        return colors.get(self.velocity, '#888888')

    @property
    def velocity_icon(self):
        icons = {
            'exploding': '🔥',
            'rising': '📈',
            'steady': '➡️',
            'declining': '📉',
        }
        return icons.get(self.velocity, '➡️')


class SavedTrend(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_trends'
    )
    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trend')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.email} saved {self.trend.title}"


class Subscription(models.Model):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan_type}"


class Comment(models.Model):
    trend = models.ForeignKey(Trend, on_delete=models.CASCADE, related_name='trend_comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_comments'
    )
    text = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author.username} on {self.trend.title[:30]}"

