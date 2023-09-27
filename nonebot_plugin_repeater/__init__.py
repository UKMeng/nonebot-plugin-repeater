import re

from nonebot import on_message, logger, require

require("nonebot_plugin_session")
require("nonebot_plugin_alconna")

from nonebot.adapters import Bot, Event
from nonebot_plugin_session import extract_session, SessionLevel

from . import config

repeater_group = config.repeater_group
shortest = config.shortest_length
blacklist = config.blacklist


m = on_message(priority=10, block=False)


last_message = {}
message_times = {}


# 消息预处理
def message_preprocess(raw_message):
    message = ""
    for seg in raw_message:
        if seg.type == "image":
            img = list(seg.values())[1]
            if "md5" in img:
                message += img["md5"]
            elif "file" in img:
                message += img["file"]
            else:
                raise ValueError("可能还没有适配，请提交issue或pr T_T")
            
            logger.debug(f"图片 {list(seg.values())[1]}")
        elif seg.type == "text":
            message += seg

    logger.debug(f"总 {message}")
    return message

@m.handle()
async def repeater(bot: Bot, event: Event):
    session = extract_session(bot, event)
    logger.debug(session)
    # 如果是私聊，跳过
    if(session.level != SessionLevel.LEVEL2):
        logger.debug(f"非群聊消息，跳过")
        m.finish()
    else:
        raw_message = event.message
        str_message = str(event.get_message())
        # 检查是否在黑名单中
        if str_message in blacklist:
            logger.debug(f'[复读姬] 检测到黑名单消息: {str_message}')
            return
        gid = str(session.id2)
        if gid in repeater_group or "all" in repeater_group:
            global last_message, message_times
            message = message_preprocess(raw_message)
            logger.debug(f'[复读姬] 这一次消息: {message}')
            logger.debug(f'[复读姬] 上一次消息: {last_message.get(gid)}')
            if last_message.get(gid) != message:
                message_times[gid] = 1
            else:
                message_times[gid] += 1
            logger.debug(f'[复读姬] 已重复次数: {message_times.get(gid)}/{config.shortest_times}')
            if message_times.get(gid) == config.shortest_times:
                logger.debug(f'[复读姬] 原始的消息: {message}')
                logger.debug(f"[复读姬] 欲发送信息: {raw_message}")
                await m.send(raw_message)
            last_message[gid] = message
