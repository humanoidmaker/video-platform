import asyncio
import sys

sys.path.insert(0, ".")

from app.database import async_session_factory, engine, Base
from app.models.user import User, UserRole
from app.utils.hashing import hash_password


async def seed_admin():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == "admin@video.local"))
        if result.scalar_one_or_none():
            print("Admin user already exists.")
            return

        admin = User(
            email="admin@video.local",
            username="admin",
            password_hash=hash_password("admin123"),
            display_name="Super Admin",
            role=UserRole.SUPERADMIN,
            is_active=True,
            email_verified=True,
        )
        session.add(admin)
        await session.commit()
        print("Admin user created: admin@video.local / admin123")


if __name__ == "__main__":
    asyncio.run(seed_admin())
