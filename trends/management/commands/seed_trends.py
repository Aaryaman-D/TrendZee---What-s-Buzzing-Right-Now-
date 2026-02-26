"""
Management command to seed demo trend data.
Run: python manage.py seed_trends
"""

from django.core.management.base import BaseCommand
from trends.models import Trend
import random


SAMPLE_TRENDS = [
    {
        "title": "AI-Generated Music Takes Over Streaming",
        "category": "music",
        "platform": "tiktok",
        "description": "AI-composed tracks are dominating TikTok trends, with creators using tools like Suno and Udio to produce chart-ready music in minutes. The debate around authenticity vs. accessibility is splitting the creator community.",
        "score": 98.2,
        "velocity": "exploding",
        "likes": 2400000,
        "shares": 890000,
        "comments": 340000,
    },
    {
        "title": "Quiet Luxury Aesthetic Returns",
        "category": "fashion",
        "platform": "instagram",
        "description": "Understated, high-quality fashion is back with force. Think neutral tones, minimal logos, and investment pieces. The anti-fast-fashion movement is driving this renewed interest in 'old money' aesthetics.",
        "score": 94.7,
        "velocity": "rising",
        "likes": 1800000,
        "shares": 620000,
        "comments": 280000,
    },
    {
        "title": "Neural Interface Gaming Demos",
        "category": "gaming",
        "platform": "youtube",
        "description": "Early demonstrations of brain-computer interface gaming are going viral. Companies like Neuralink adjacent startups are showcasing rudimentary but mind-bending gameplay controlled purely by thought.",
        "score": 91.3,
        "velocity": "exploding",
        "likes": 3200000,
        "shares": 1200000,
        "comments": 560000,
    },
    {
        "title": "Deinfluencing 2.0 — Anti-Haul Culture",
        "category": "entertainment",
        "platform": "tiktok",
        "description": "Creators are doubling down on telling audiences what NOT to buy. The anti-haul genre is growing as consumers push back against overconsumption, with some creators gaining millions of followers for honest product reviews.",
        "score": 87.9,
        "velocity": "rising",
        "likes": 1400000,
        "shares": 780000,
        "comments": 410000,
    },
    {
        "title": "SpaceX Starship Commercial Launch Reaction",
        "category": "science",
        "platform": "twitter",
        "description": "The first commercial passengers aboard Starship generated massive social media engagement. Live reactions, debate about democratizing space travel, and viral clips of the launch are dominating feeds across platforms.",
        "score": 85.4,
        "velocity": "rising",
        "likes": 5600000,
        "shares": 2100000,
        "comments": 890000,
    },
    {
        "title": "Microlearning Business Content",
        "category": "business",
        "platform": "linkedin",
        "description": "60-second business strategy breakdowns are outperforming long-form LinkedIn posts. Creators who distill complex frameworks into tight visual formats are gaining massive professional following growth.",
        "score": 82.1,
        "velocity": "rising",
        "likes": 890000,
        "shares": 340000,
        "comments": 120000,
    },
    {
        "title": "Cottagecore Cuisine Revival",
        "category": "food",
        "platform": "instagram",
        "description": "Rustic, homemade aesthetic cooking content is surging. Think sourdough, foraged ingredients, preserved goods, and farmhouse-style presentations. The movement represents a retreat from hypermodern food content.",
        "score": 79.6,
        "velocity": "steady",
        "likes": 1100000,
        "shares": 430000,
        "comments": 195000,
    },
    {
        "title": "Retro Tech Aesthetic — Landline Comeback",
        "category": "technology",
        "platform": "tiktok",
        "description": "Gen Z ironic nostalgia for pre-smartphone technology is driving demand for vintage tech. Landline phones, film cameras, and early internet aesthetics are being rebranded as premium lifestyle choices.",
        "score": 76.3,
        "velocity": "steady",
        "likes": 920000,
        "shares": 380000,
        "comments": 167000,
    },
    {
        "title": "NBA Trade Deadline Reactions",
        "category": "sports",
        "platform": "twitter",
        "description": "This year's deadline produced blockbuster moves that reshuffled title contenders overnight. Fan takes, analyst reactions, and highlight packages are generating record engagement in sports discourse.",
        "score": 88.7,
        "velocity": "exploding",
        "likes": 4200000,
        "shares": 1800000,
        "comments": 920000,
    },
    {
        "title": "Political Satire on Threads",
        "category": "politics",
        "platform": "threads",
        "description": "Short-form political commentary is finding a new home on Threads. Satirical takes and meme formats are spreading rapidly, with several politically-neutral humor accounts reaching 1M+ followers within weeks.",
        "score": 72.8,
        "velocity": "rising",
        "likes": 780000,
        "shares": 290000,
        "comments": 145000,
    },
    {
        "title": "Open-Source AI Model Leaderboards",
        "category": "technology",
        "platform": "reddit",
        "description": "Community-driven benchmarks for open source LLMs are becoming must-follow resources for developers and tech enthusiasts. Weekly model releases and benchmark comparisons drive massive Reddit and Twitter engagement.",
        "score": 83.5,
        "velocity": "rising",
        "likes": 680000,
        "shares": 420000,
        "comments": 290000,
    },
    {
        "title": "HIIT vs. Zone 2 Training Debate",
        "category": "food",
        "platform": "youtube",
        "description": "Fitness content creators and sports scientists are debating optimal training methodologies. Zone 2 cardio advocates are gaining significant ground, with long-form explainer content accumulating millions of views.",
        "score": 69.4,
        "velocity": "steady",
        "likes": 560000,
        "shares": 180000,
        "comments": 98000,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample trend data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing trends before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            Trend.objects.all().delete()
            self.stdout.write(self.style.WARNING('Cleared existing trends.'))

        created_count = 0
        for trend_data in SAMPLE_TRENDS:
            trend, created = Trend.objects.get_or_create(
                title=trend_data['title'],
                defaults=trend_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✓ Created: {trend.title}")
            else:
                self.stdout.write(f"  — Already exists: {trend.title}")

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully seeded {created_count} new trends. '
            f'Total in database: {Trend.objects.count()}'
        ))
