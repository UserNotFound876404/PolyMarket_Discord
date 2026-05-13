import motor.motor_asyncio
import os

class MarketModel:
    def __init__(self):
        # Pulling the URI from your .env
        uri = os.getenv('mongoDB_uri')
        self.client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self.client["gamble_bot"]
        self.users = self.db["users"]

    async def create_account(self, user_id):
    # Check if user already exists
        existing_user = await self.users.find_one({"_id": str(user_id)})
        
        if existing_user:
            return False # Account already exists
        
        # Create new account with a starter bonus
        await self.users.insert_one({
            "_id": str(user_id),
            "balance": 500,  # Starting money
        })
        return True

    async def get_balance(self, user_id):
        user = await self.users.find_one({"_id": str(user_id)})
        if not user:
            # Starting cash for new players
            await self.users.insert_one({"_id": str(user_id), "balance": 500})
            return 500
        return user['balance']

    async def update_balance(self, user_id, amount):
        """Positive amount to add, negative to subtract"""
        await self.users.update_one(
            {"_id": str(user_id)},
            {"$inc": {"balance": amount}},
            upsert=True
        )