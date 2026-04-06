import asyncio
import sys
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, ".")

from app.database import async_session_factory, engine, Base
from app.models.user import User, UserRole
from app.models.channel import Channel
from app.models.category import Category
from app.models.video import Video, VideoStatus, VideoVisibility
from app.models.playlist import Playlist, PlaylistVisibility
from app.models.playlist_item import PlaylistItem
from app.models.comment import Comment
from app.models.tag import Tag
from app.models.subscription import Subscription
from app.utils.hashing import hash_password


CREATORS = [
    ("bytecraft", "ByteCraft", "arjun@video.local", "Arjun Desai", "Tech reviews, tutorials, and programming guides."),
    ("spicenest", "Spice Nest Kitchen", "kavita@video.local", "Kavita Rao", "Authentic Indian recipes and cooking tips."),
    ("dailyreps", "Daily Reps", "sanjay@video.local", "Sanjay Gupta", "Home workouts, fitness tips, and healthy living."),
    ("devdiary", "Dev Diary", "divya@video.local", "Divya Iyer", "Programming tutorials and system design."),
    ("wanderdesi", "Wander Desi", "vivek@video.local", "Vivek Joshi", "Exploring the beauty of India one trip at a time."),
]

CATEGORIES_DATA = [
    ("Education", "education", "Tutorials and learning content", "graduation-cap", 0),
    ("Entertainment", "entertainment", "Fun and entertaining videos", "tv", 1),
    ("Technology", "technology", "Tech reviews and guides", "cpu", 2),
    ("Music", "music", "Music videos and performances", "music", 3),
    ("Gaming", "gaming", "Game streams and walkthroughs", "gamepad-2", 4),
    ("Cooking", "cooking", "Recipes and cooking tutorials", "chef-hat", 5),
    ("Fitness", "fitness", "Workouts and health tips", "dumbbell", 6),
    ("Travel", "travel", "Travel vlogs and guides", "plane", 7),
]

VIDEOS = {
    "bytecraft": [
        ("Python for Beginners — Full Course", "python-tutorial-2024", "Technology", "Learn Python from scratch. This comprehensive tutorial covers everything from basics to advanced topics including OOP, file handling, and web scraping.", 2700, 245000, 18200),
        ("Building a REST API Step by Step", "rest-api-from-scratch", "Technology", "Step-by-step guide to building a production-ready REST API using Python and PostgreSQL.", 1800, 128000, 9800),
        ("Docker Essentials for Developers", "docker-for-beginners", "Technology", "Everything you need to know about Docker containers, images, and Docker Compose.", 2400, 186000, 14500),
        ("Linux Commands Every Developer Should Know", "linux-commands-devs", "Technology", "Master the essential Linux commands used daily by professional developers.", 1200, 97000, 7200),
    ],
    "spicenest": [
        ("Creamy Butter Chicken at Home", "butter-chicken-recipe", "Cooking", "Learn to make creamy, rich butter chicken at home that tastes better than restaurants.", 900, 412000, 32000),
        ("Perfect Crispy Dosa from Scratch", "south-indian-dosa", "Cooking", "Crispy dosa recipe with step-by-step fermentation guide and three chutneys.", 720, 289000, 21000),
        ("Dum Biryani Made Simple", "easy-biryani-home", "Cooking", "Hyderabadi style dum biryani made simple. Fragrant rice with tender chicken.", 1080, 356000, 28000),
        ("Quick Indian Snacks in 10 Minutes", "10-minute-snacks", "Cooking", "Quick and easy Indian snack recipes perfect for tea time and unexpected guests.", 600, 198000, 15000),
    ],
    "dailyreps": [
        ("30 Min Full Body Workout — No Equipment", "30-min-full-body", "Fitness", "No equipment needed! Complete full body workout you can do at home.", 1800, 167000, 12400),
        ("Beginner Yoga Poses and Breathing", "yoga-beginners-guide", "Fitness", "Start your yoga journey with these fundamental poses and breathing techniques.", 2100, 234000, 18700),
        ("Setting Up a Home Gym on a Budget", "home-gym-setup", "Fitness", "Build the perfect home gym on a budget. Equipment reviews and layout tips.", 1500, 89000, 6800),
    ],
    "devdiary": [
        ("React Hooks and Components — Crash Course", "react-18-crash-course", "Education", "Learn React with hooks, context, and the latest features in under an hour.", 3600, 523000, 41200),
        ("System Design Concepts Explained", "system-design-interview", "Education", "Master system design concepts for technical interviews at top companies.", 2700, 312000, 24500),
        ("Data Structures in Java — A Visual Guide", "data-structures-java", "Education", "Comprehensive guide to arrays, linked lists, trees, graphs, and hash maps.", 3000, 198000, 15600),
        ("Git and Version Control — Complete Tutorial", "git-github-tutorial", "Education", "From git init to advanced branching strategies and CI/CD workflows.", 1800, 267000, 20100),
    ],
    "wanderdesi": [
        ("Kerala Backwaters Houseboat Experience", "kerala-backwaters-vlog", "Travel", "Houseboat experience through the serene backwaters of Alleppey, Kerala.", 1200, 145000, 11200),
        ("Rajasthan Road Trip — Forts and Deserts", "rajasthan-road-trip", "Travel", "Jaipur to Udaipur — exploring forts, palaces, and the Thar Desert.", 1500, 178000, 13500),
        ("Goa Travel Guide on a Budget", "goa-budget-travel", "Travel", "How to enjoy Goa without breaking the bank. Best beaches, food, and stays.", 900, 234000, 18000),
        ("Trekking in Himachal Pradesh", "himachal-trek-vlog", "Travel", "Triund trek adventure with stunning views of the Dhauladhar range.", 1080, 112000, 8700),
    ],
}

TAGS_DATA = ["python", "react", "cooking", "fitness", "travel", "tutorial", "vlog", "india", "programming", "recipe"]

COMMENTS = [
    "Great tutorial, very helpful! Learned so much.",
    "Can you make a video on web frameworks next?",
    "This recipe turned out amazing, thanks!",
    "Finally someone explained this properly. Subscribed!",
    "Best fitness channel on the platform. Keep it up!",
    "I followed this tutorial and got my first API running!",
    "The visuals in this vlog are stunning. What camera do you use?",
    "Please make a part 2 of this series.",
    "Tried the biryani recipe today. Family loved it!",
    "Your teaching style is incredible. So clear and concise.",
    "Been looking for this exact content. Thank you!",
    "This workout really gets the heart pumping. Great job!",
    "India has so many beautiful places. Adding to my bucket list.",
    "Explained complex concepts in the simplest way possible.",
    "I switched careers after watching your Python series. Thank you!",
    "The tips about Docker volumes saved me hours of debugging.",
    "My favorite cooking channel. Every recipe is a winner.",
    "Could you cover container orchestration in your next video?",
    "Just completed the full body workout. Feeling great!",
    "Goa on a budget is exactly what I needed. Planning my trip now.",
    "How long did the trek take in total?",
    "Love the energy in your videos. Always puts me in a good mood.",
    "Sharing this with my study group. Gold content!",
    "The dosa came out perfect on my third try. Practice makes perfect!",
    "React hooks finally make sense after this video.",
    "Your Rajasthan video made me book tickets immediately!",
    "Subscribed and turned on notifications. Don't want to miss anything.",
    "This is better than most paid courses out there.",
    "The background music in this vlog is perfect. What track is it?",
    "Tried the home gym setup. Best investment I've made this year.",
]


async def seed_sample_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(select(Category))
        if result.scalars().first():
            print("Sample data already exists.")
            return

        now = datetime.now(timezone.utc)

        # 1. Create categories
        cat_map = {}
        for name, slug, desc, icon, sort in CATEGORIES_DATA:
            cat = Category(name=name, slug=slug, description=desc, icon=icon, sort_order=sort)
            session.add(cat)
            cat_map[name] = cat
        await session.flush()
        print(f"Created {len(CATEGORIES_DATA)} categories")

        # 2. Create tags
        tag_map = {}
        for tag_name in TAGS_DATA:
            tag = Tag(name=tag_name, slug=tag_name)
            session.add(tag)
            tag_map[tag_name] = tag
        await session.flush()
        print(f"Created {len(TAGS_DATA)} tags")

        # 3. Create creators and channels
        creator_users = {}
        channel_map = {}
        for handle, ch_name, email, display_name, bio in CREATORS:
            user = User(
                email=email, username=handle, password_hash=hash_password("creator123"),
                display_name=display_name, role=UserRole.CREATOR, is_active=True, email_verified=True, bio=bio,
            )
            session.add(user)
            await session.flush()
            creator_users[handle] = user

            subs = random.randint(10000, 80000)
            channel = Channel(
                owner_id=user.id, handle=handle, name=ch_name,
                description=bio, subscriber_count=subs,
                is_verified=handle in ("bytecraft", "devdiary"),
                is_active=True,
            )
            session.add(channel)
            await session.flush()
            channel_map[handle] = channel
        print(f"Created {len(CREATORS)} creators with channels")

        # 4. Create viewer users
        viewers = []
        viewer_data = [
            ("viewer1", "Nikhil Reddy", "nikhil@video.local"),
            ("viewer2", "Pallavi Menon", "pallavi@video.local"),
            ("viewer3", "Tarun Bhat", "tarun@video.local"),
        ]
        for username, display_name, email in viewer_data:
            user = User(
                email=email, username=username, password_hash=hash_password("viewer123"),
                display_name=display_name, role=UserRole.VIEWER, is_active=True, email_verified=True,
            )
            session.add(user)
            viewers.append(user)
        await session.flush()
        print("Created 3 viewer users")

        # 5. Create videos
        all_videos = []
        for handle, videos_list in VIDEOS.items():
            channel = channel_map[handle]
            for i, (title, slug, cat_name, desc, duration, views, likes) in enumerate(videos_list):
                cat = cat_map.get(cat_name)
                video = Video(
                    channel_id=channel.id, category_id=cat.id if cat else None,
                    title=title, slug=slug, description=desc,
                    status=VideoStatus.READY, visibility=VideoVisibility.PUBLIC,
                    duration=float(duration),
                    thumbnail_url=f"https://placehold.co/640x360/1a1f36/c8a96e?text={slug}",
                    view_count=views, like_count=likes,
                    dislike_count=int(likes * 0.02),
                    comment_count=random.randint(50, 500),
                    published_at=now - timedelta(days=random.randint(1, 180)),
                )
                session.add(video)
                all_videos.append(video)

            # Update channel video count
            channel.video_count = len(videos_list)
            channel.total_views = sum(v[5] for v in videos_list)

        await session.flush()
        print(f"Created {len(all_videos)} videos")

        # 6. Create playlists
        playlists = [
            ("Python Mastery", "python-mastery", "bytecraft", [0, 1]),
            ("Indian Cuisine Collection", "indian-cuisine", "spicenest", [0, 1, 2]),
            ("Web Dev Essentials", "web-dev-2024", "devdiary", [0, 3]),
        ]

        # Build per-channel video lists
        channel_videos = {}
        vid_idx = 0
        for handle in VIDEOS:
            count = len(VIDEOS[handle])
            channel_videos[handle] = all_videos[vid_idx:vid_idx + count]
            vid_idx += count

        for title, slug, handle, video_idxs in playlists:
            channel = channel_map[handle]
            vids = channel_videos[handle]
            playlist = Playlist(
                channel_id=channel.id, title=title, slug=slug,
                description=f"Curated playlist by {handle}",
                visibility=PlaylistVisibility.PUBLIC,
                video_count=len(video_idxs),
            )
            session.add(playlist)
            await session.flush()
            for pos, vi in enumerate(video_idxs):
                if vi < len(vids):
                    pi = PlaylistItem(playlist_id=playlist.id, video_id=vids[vi].id, position=pos)
                    session.add(pi)
        print(f"Created {len(playlists)} playlists")

        # 7. Create comments
        all_users = list(creator_users.values()) + viewers
        for i, comment_text in enumerate(COMMENTS):
            video = all_videos[i % len(all_videos)]
            user = all_users[i % len(all_users)]
            comment = Comment(
                video_id=video.id, user_id=user.id, content=comment_text,
                like_count=random.randint(0, 50),
            )
            session.add(comment)
        print(f"Created {len(COMMENTS)} comments")

        # 8. Subscriptions (viewers subscribe to channels)
        for viewer in viewers:
            for handle, channel in channel_map.items():
                if random.random() > 0.3:
                    sub = Subscription(subscriber_id=viewer.id, channel_id=channel.id)
                    session.add(sub)
        print("Created subscriptions")

        await session.commit()
        print("Video platform sample data seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_sample_data())
