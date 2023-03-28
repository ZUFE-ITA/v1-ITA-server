import os
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from ..database import TeamMail

class EmailSchema(BaseModel):
    email: list[EmailStr]


""" send mail """
class Sender:

    conf: ConnectionConfig
    fm: FastMail

    @classmethod
    async def New(cls, team:str = None):
        obj = cls()
        obj.conf = await TeamMail.get_config(team)
        obj.fm = FastMail(obj.conf)
        return obj
    
    async def send(self, *, subject: str, to: EmailSchema, body: str, subtype: str="plain"):
        _type = MessageType.html if subtype == 'html' else MessageType.plain
        message = MessageSchema(
            subject = subject,
            recipients = to.dict().get("email"),
            body = body,
            subtype = _type
        )
        await self.fm.send_message(message)

SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
TEMPLATES_PATH = os.path.join(SCRIPT_PATH, "../templates")

async def send_verify_code_mail(code, addr, reason=''):
    # 加载邮件的html模板
    with open(os.path.join(TEMPLATES_PATH, "./activate_email.html"), 'r+', encoding='utf8') as f:
        ACTIVATE_EMAIL_TEMPLATE = f.read()
    sender =  await Sender.New(None)
    await sender.send(
        subject = f"{reason}IDIM.cc",
        to = EmailSchema(email=[addr]),
        body = ACTIVATE_EMAIL_TEMPLATE.format(code=code),
        subtype = "html"
    )
