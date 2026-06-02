import logging

from django.utils import timezone

from djangoblog.utils import cache, get_blog_setting
from .models import Category, Article

logger = logging.getLogger(__name__)


def seo_processor(requests):
    key = 'seo_processor'
    value = cache.get(key)
    if value:
        # 更新动态值（不需要缓存的内容）
        value['SITE_BASE_URL'] = requests.scheme + '://' + requests.get_host() + '/'
        value['CURRENT_YEAR'] = timezone.now().year
        return value
    else:
        logger.info('set processor cache.')
        setting = get_blog_setting()

        # 优化查询：预加载关联数据
        nav_category_list = Category.objects.all()
        nav_pages = Article.objects.filter(
            type='p',
            status='p'
        )

        value = {
            'SITE_NAME': setting.site_name,
            'SHOW_GOOGLE_ADSENSE': setting.show_google_adsense,
            'GOOGLE_ADSENSE_CODES': setting.google_adsense_codes,
            'SITE_SEO_DESCRIPTION': setting.site_seo_description,
            'SITE_DESCRIPTION': setting.site_description,
            'SITE_KEYWORDS': setting.site_keywords,
            'SITE_BASE_URL': requests.scheme + '://' + requests.get_host() + '/',
            'ARTICLE_SUB_LENGTH': setting.article_sub_length,
            'nav_category_list': nav_category_list,  # 保持QuerySet
            'nav_pages': nav_pages,  # 保持QuerySet
            'OPEN_SITE_COMMENT': setting.open_site_comment,
            'BEIAN_CODE': setting.beian_code,
            'ANALYTICS_CODE': setting.analytics_code,
            "BEIAN_CODE_GONGAN": setting.gongan_beiancode,
            "SHOW_GONGAN_CODE": setting.show_gongan_code,
            "CURRENT_YEAR": timezone.now().year,
            "GLOBAL_HEADER": setting.global_header,
            "GLOBAL_FOOTER": setting.global_footer,
            "COMMENT_NEED_REVIEW": setting.comment_need_review,
            "COLOR_SCHEME": setting.color_scheme,
            "PORTFOLIO_HERO_TITLE": setting.portfolio_hero_title,
            "PORTFOLIO_HERO_SUBTITLE": setting.portfolio_hero_subtitle,
            "PORTFOLIO_SKILLS": setting.portfolio_skills,
            "PORTFOLIO_EXPERIENCE": setting.portfolio_experience,
            "PORTFOLIO_EDUCATION": setting.portfolio_education,
            "PORTFOLIO_CONTACT_EMAIL": setting.portfolio_contact_email,
            "PORTFOLIO_GITHUB": setting.portfolio_github,
            "PORTFOLIO_LINKEDIN": setting.portfolio_linkedin,
            # 简历数据
            "RESUME_NAME": setting.resume_name,
            "RESUME_AVATAR": setting.resume_avatar.url if setting.resume_avatar else '',
            "RESUME_AGE": setting.resume_age,
            "RESUME_YEARS_EXPERIENCE": setting.resume_years_experience,
            "RESUME_EDUCATION": setting.get_resume_education_display(),
            "RESUME_PHONE": setting.resume_phone,
            "RESUME_WECHAT": setting.resume_wechat,
            "RESUME_JOB_STATUS": setting.get_resume_job_status_display(),
            "RESUME_JOB_EXPECTATION": setting.resume_job_expectation,
            "RESUME_STRENGTHS": setting.resume_strengths,
            "RESUME_WORK_EXPERIENCE": setting.resume_work_experience,
            "RESUME_RECENT_PROJECTS": setting.resume_recent_projects,
        }
        cache.set(key, value, 60 * 60 * 10)
        return value
