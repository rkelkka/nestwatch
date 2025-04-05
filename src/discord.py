import os
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed

DISCORD_WEBHOOK_URL=os.getenv("DISCORD_WEBHOOK_URL")

def postActivity(stream_title, stream_url, frame_img):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)

    webhook.add_file(file=frame_img, filename="captured.jpg")

    embed = DiscordEmbed(title=f"Activity spotted at {stream_title}", description=stream_url , color="f3964a")
    embed.set_thumbnail(url="attachment://captured.jpg")

    webhook.add_embed(embed)
    response = webhook.execute()

def postGone(stream_title):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=f"{stream_title} nest now empty :(")
    response = webhook.execute()


#if __name__ == '__main__':
#    with open("osprey.jpg", "rb") as f:
#        postActivity("Saaksi 3", "http://youtube.com", f)
