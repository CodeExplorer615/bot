import asyncio
from pas import bot as bot1
from mvdpasbot import bot as bot2

async def main():
    await asyncio.gather(
        bot1.polling(non_stop=True),
        bot2.polling(non_stop=True)
    )

if __name__ == "__main__":
    asyncio.run(main())

