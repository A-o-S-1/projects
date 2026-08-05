from .models import SchoolInfo


def school_info(request):
    """
    Makes `school_info` available in every template automatically, so
    base.html's navbar/footer can render phone numbers, socials, etc.
    without every view having to pass it in its own context.
    """
    return {"school_info": SchoolInfo.load()}
