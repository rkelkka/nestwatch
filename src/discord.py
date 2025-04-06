import os
import requests
from discord_webhook import DiscordWebhook, DiscordEmbed
from discord_webhook.constants import MessageFlags

DISCORD_WEBHOOK_URL=os.getenv("DISCORD_WEBHOOK_URL")

def postInit(stream_title_url_str, prompt):
    desc = f"Streams:\n{stream_title_url_str}\nPrompt: \"{prompt}\""
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=desc, flags=MessageFlags.SUPPRESS_EMBEDS.value)
    response = webhook.execute()

def postActivity(stream_title, stream_url, frame_img, answer):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)

    webhook.add_file(file=frame_img, filename="captured.jpg")

    desc = f"{stream_url}"

    embed = DiscordEmbed(title=f"Activity spotted at {stream_title}", description=desc, color="f3964a")
    embed.set_timestamp()
    embed.set_image(url="attachment://captured.jpg")
    # footer does not render links..
    embed.set_footer(answer)
    embed.set_author(name=stream_title, url=stream_url)

    webhook.add_embed(embed)
    response = webhook.execute()

def postGone(stream_title):
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=f"{stream_title} nest is now empty :empty_nest:")
    response = webhook.execute()


#if __name__ == '__main__':
#    with open("osprey.jpg", "rb") as f:
#        postActivity("Saaksi 3", "http://youtube.com", f)
