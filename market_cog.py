import discord
from discord.ext import commands
from model import MarketModel
import random

class MarketController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.model = MarketModel()

    @commands.command(aliases=['register', 'start'])
    async def setup(self, ctx):
        # Call the model to try and create the account
        success = await self.model.create_account(ctx.author.id)
        
        if success:
            await ctx.send(f"🎊 **Welcome to PolyMart Games, {ctx.author.name}!**\nYour account has been created with a **$500** starter bonus!")
        else:
            await ctx.send(f"⚠️ You already have an account, {ctx.author.name}! Use `=balance` to check your funds.")

    @commands.command()
    async def coinflip(self, ctx, amount: int, choice: str= None):
        if amount is None or choice is None:
            return await ctx.send("Please specify an amount to bet. Example: `=coinflip 50 heads`")
        if amount <= 0:
            return await ctx.send("You can't flip air! Bet at least $1.")
        if choice and choice.lower() not in ['heads', 'tails']:
            return await ctx.send("Choose `heads` or `tails` (or leave it blank for random).")
        user_bal = await self.model.get_balance(ctx.author.id)
        if user_bal < amount:
            return await ctx.send("❌ You don't have enough coins for this flip.")

        user_choice = choice.lower()
        actual_result = random.choice(['heads', 'tails'])
        
        win = (user_choice == actual_result)
        # 3. Update Database
        change = amount if win else -amount
        await self.model.update_balance(ctx.author.id, change)

        # 4. The "View" (Visual feedback)
        if win:
            await ctx.send(f"📈 It's **{actual_result.upper()}**! You won **${amount}**!")
        else:
            await ctx.send(f"💀 It's **{actual_result.upper()}**... You lost **${amount}**.")

    # Add this inside your MarketController class in market_cog.py
    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user) # 1 use every 300 seconds (5 mins) per user
    async def work(self, ctx):
        salary = random.randint(10, 60)
        await self.model.update_balance(ctx.author.id, salary)
        await ctx.send(f"💰 You worked at cotton farm and earned **${salary}**!")
        
    @work.error
    async def work_error(self, ctx, error):
        # Check if the error is specifically a Cooldown error
        if isinstance(error, commands.CommandOnCooldown):
            # Calculate minutes and seconds remaining
            minutes, seconds = divmod(error.retry_after, 60)
            
            # Send a friendly message to the user
            await ctx.send(
                f"⌛ **Take a break!** You are exhausted from the farm.\n"
                f"You can work again in **{int(minutes)}m {int(seconds)}s**."
            )
        else:
            # If it's a different error (like a database issue), 
            # this makes sure it still shows up in your console.
            raise error

    @commands.command(aliases=['bal'])
    async def balance(self, ctx):
        # 1. Use the correct async method from your new Model
        bal = await self.model.get_balance(ctx.author.id)
        
        # 2. 'bal' is now just a number, so we use it directly
        await ctx.send(f"💰 **{ctx.author.name}'s Balance:** ${bal}")

    @commands.command()
    async def startpool(self, ctx, amount: int,*, question: str):

        for bets in self.bet_data.values():
            if bets == ctx.author.id:
                return await ctx.send("❌ You already have an active bet! Please stop it before starting a new one.") 

        # 1. Create the UI
        if amount <= 0:
            return await ctx.send("❌ The bet amount must be greater than 0!")
        
        embed = discord.Embed(
            title="🎲 Community Bet Started!",
            description=f"**{question}**\n\nReact with ✅ for **YES** ({amount})\nReact with ❌ for **NO** ({amount})",
            color=discord.Color.blue()
        )
        bet_msg = await ctx.send(embed=embed)

        # 2. Add the "Buttons" (Emojis)
        await bet_msg.add_reaction("✅")
        await bet_msg.add_reaction("❌")

        # 3. Store the bet state (Simplified for this example)
        self.active_bet_id = bet_msg.id
        self.bet_data = {"yes": [], "no": [], "amount": amount, "creator": ctx.author.id}

    @commands.command()
    async def stoppool(self, ctx, winner: str):
        # 1. Security Check: Only the creator can close it
        if not hasattr(self, 'active_bet_id'):
            return await ctx.send("❌ There is no active pool to stop.")
        
        if ctx.author.id != self.bet_data["creator"]:
            return await ctx.send("🚫 Only the person who started the bet can stop it!")

        winner = winner.lower()
        if winner not in ['yes', 'no']:
            return await ctx.send("Usage: `=stoppool yes` or `=stoppool no`")

        # 2. Calculate the Winnings
        winners_list = self.bet_data[winner]
        losers_list = self.bet_data["no" if winner == "yes" else "yes"]
        
        total_pot = (len(winners_list) + len(losers_list)) * self.bet_data["amount"]

        if not winners_list:
            await ctx.send(f"💀 The winner was **{winner.upper()}**, but nobody bet on that! The house takes the pot.")
        else:
            # 3. Distribute the money
            # Simple version: Split the total pot equally among all winners
            payout = total_pot // len(winners_list)
            
            for user_id in winners_list:
                await self.model.update_balance(user_id, payout)

            await ctx.send(
                f"🎊 **Bet Resolved!** The winner is **{winner.upper()}**!\n"
                f"💰 Total Pot of **${total_pot}** split among {len(winners_list)} winner(s).\n"
                f"Each winner received **${payout}**!"
            )

        # 4. Clear the active bet so a new one can start
        del self.active_bet_id
        self.bet_data = None



    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # 1. Ignore the bot's own reactions
        if user.bot:
            return

        # 2. Check if this is the active bet message
        if not hasattr(self, 'active_bet_id') or reaction.message.id != self.active_bet_id:
            return

        # 3. Handle the logic based on emoji
        if str(reaction.emoji) in ["✅", "❌"]:
            # Check balance
            balance = await self.model.get_balance(user.id)
            bet_amount = self.bet_data["amount"]

            if balance < bet_amount:
                # Remove their reaction if they are too broke
                await reaction.message.remove_reaction(reaction.emoji, user)
                return await user.send("❌ You don't have enough money to join this bet!")

            # Deduct money and track the bet
            await self.model.update_balance(user.id, -bet_amount)
            
            side = "yes" if str(reaction.emoji) == "✅" else "no"
            self.bet_data[side].append(user.id)
            
            # (Optional) Send a DM to confirm
            await user.send(f"👍 You've placed ${bet_amount} on **{side.upper()}**!")

async def setup(bot):
    await bot.add_cog(MarketController(bot))