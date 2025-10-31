# views.py
from threading import Thread
import time
from typing import Dict, Set
# Уберите или закомментируйте эту строку, если вызывает проблемы:
# from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
import os
import json
import asyncio
import requests
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
import logging
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate  # Добавьте authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from datetime import datetime
from django.utils import timezone
from datetime import timedelta

from .telegram_bot import TelegramNotifier, TelegramBot
from .models import CertificateTemplate, VolunteerApplication, OrganizerApplication, Certificate

# Уберите эти строки из views.py и перенесите в telegram_bot.py:
# class TelegramBot, class TelegramNotifier, telegram_bot, telegram_notifier, start_telegram_bot()
# Configure logging
logger = logging.getLogger(__name__)

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = getattr(
    settings, 'TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
TELEGRAM_CHAT_ID = getattr(settings, 'TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')

# Mock data (converted from mock.js)
site_data = {
    'statistics': {
        'treesPlanted': 156789,
        'targetTrees': 500000,
        'activeUsers': 2340,
        'daysUntilPlatformLaunch': 45,
        'totalDonations': 8540000
    },
    'navigation': {
        'ru': {
            'about': 'О нас',
            'reports': 'Отчеты',
            'individuals': 'Частным лицам',
            'volunteers': 'Волонтерам',
            'organizations': 'Организациям',
            'login': 'Вход / регистрация',
            'language': 'Рус'
        },
        'kz': {
            'about': 'Біз туралы',
            'reports': 'Есептер',
            'individuals': 'Жеке тұлғаларға',
            'volunteers': 'Ерікті қызметкерлер',
            'organizations': 'Ұйымдарға',
            'login': 'Кіру / тіркелу',
            'language': 'Қаз'
        },
        'en': {
            'about': 'About Us',
            'reports': 'Reports',
            'individuals': 'For Individuals',
            'volunteers': 'Volunteers',
            'organizations': 'Organizations',
            'login': 'Login / Register',
            'language': 'Eng'
        }
    },
    'hero': {
        'ru': {
            'mainText': 'Каждое дерево - это шаг к зеленому будущему Казахстана',
            'subText': 'Присоединяйтесь к нашей миссии по восстановлению лесов и борьбе с изменением климата',
            'ctaButton': 'Посадить дерево',
            'treesText': 'деревьев',
            'targetText': 'Цель',
            'usersText': 'Участников проекта',
            'usersCount': 'человек',
            'daysText': 'До запуска посадочного сезона',
            'daysCount': 'дней'
        },
        'kz': {
            'mainText': 'Әр ағаш - Қазақстанның жасыл болашағына қадам',
            'subText': 'Орманды қалпына келтіру және климаттық өзгерістермен күресу миссиямызға қосылыңыз',
            'ctaButton': 'Ағаш отырғызу',
            'treesText': 'ағаш',
            'targetText': 'Мақсат',
            'usersText': 'Жоба қатысушылары',
            'usersCount': 'адам',
            'daysText': 'Отырғызу маусымының басталуына дейін',
            'daysCount': 'күн'
        },
        'en': {
            'mainText': 'Every tree is a step towards Kazakhstan\'s green future',
            'subText': 'Join our mission to restore forests and fight climate change',
            'ctaButton': 'Plant a Tree',
            'treesText': 'trees',
            'targetText': 'Target',
            'usersText': 'Project participants',
            'usersCount': 'people',
            'daysText': 'Until planting season starts',
            'daysCount': 'days'
        }
    },
    'importance': {
        'first': {
            'ru': {
                'header': 'Наследие Старого дуба',
                'subtext': 'Один дуб может поддерживать более 500 видов дикой природы на протяжении всей своей жизни.',
                'story': '"Древний дуб на площади моей деревни был свидетелем того, как поколения детей играли под его ветвями, точно так же, как я играла со своими внуками".',
                'author': 'Елена, 72 года, Маленькой деревня в Казахстане'
            },
            'kz': {
                'header': 'Ескі Еменнің Мұрасы',
                'subtext': 'Бір емен ағашы өмір бойы жабайы табиғаттың 500-ден астам түрін қолдай алады.',
                'story': '"Менің ауылымның алаңындағы ежелгі емен ағашы немерелеріммен жасағандай, оның бұтақтарының астында ойнап жүрген балалардың ұрпақтарының куәсі болды."',
                'author': 'Елена, 72 жаста, кішкентай қазақ ауылынан'
            },
            'en': {
                'header': 'The Old Oak\'s Legacy',
                'subtext': 'A single oak tree can support over 500 species of wildlife throughout its lifetime.',
                'story': '"The ancient oak in my village square has witnessed generations of children playing beneath its branches, just as I did with my grandchildren."',
                'author': 'Elena, 72, from a small Kazakh village'
            },
        },
        'second': {
            'ru': {
                'header': 'Дыхание леса',
                'subtext': 'Акр зрелых деревьев может обеспечить кислородом 18 человек на целый год',
                'story': '"После того, как врачи сказали, что моя астма будет ограничивать мои возможности, мы переехали поближе к лесу. Теперь я свободно дышу среди деревьев, которые дают мне жизнь"',
                'author': 'Амир, 34 года, Алмата'
            },
            'kz': {
                'header': 'Орман Тынысы',
                'subtext': 'Бір акр жетілген ағаштар бір жыл ішінде 18 адамды оттегімен қамтамасыз ете алады.',
                'story': '"Дәрігерлер демікпем мені шектейтінін айтқаннан кейін, біз орманға жақындадық. Енді мен өмір сыйлайтын ағаштардың арасында еркін дем аламын."',
                'author': 'Әмір, 34 жаста, Алматыдан'
            },
            'en': {
                'header': 'The Forest\'s Breath',
                'subtext': 'An acre of mature trees can provide oxygen for 18 people for an entire year.',
                'story': '"After the doctors said my asthma would limit me, we moved near a forest. Now I breathe freely among the trees that give me life."',
                'author': 'Amir, 34, from Almaty'
            },
        },
        'third': {
            'ru': {
                'header': 'Тень надежды',
                'subtext': 'Деревья могут снизить температуру в городах до 8°С, создавая жизненно важные оазисы в потеплевших городах',
                'story': '"Во время сильной жары единственным местом, где мой новорожденный мог спокойно спать, была тень старого дерева возле нашей квартиры"',
                'author': 'Аиша, 28 лет, Нур-Султан'
            },
            'kz': {
                'header': 'Үміт Көлеңкесі',
                'subtext': 'Ағаштар қалалардағы температураны Цельсий бойынша 8° C-қа дейін төмендетіп, жылынатын қалаларда өмірлік маңызды оазистер жасай алады.',
                'story': '"Аптап ыстық кезінде менің жаңа туған нәрестем тыныш ұйықтай алатын жалғыз орын пәтеріміздің сыртындағы ескі ағаштың көлеңкесінде болды."',
                'author': 'Айша, 28 жаста, Нұр-Сұлтаннан'
            },
            'en': {
                'header': 'The Shade of Hope',
                'subtext': 'Trees can reduce urban temperatures by up to 8° Celsius, creating vital oases in warming cities.',
                'story': '"During the heatwave, the only place my newborn could sleep peacefully was under the shade of the old tree outside our apartment."',
                'author': 'Aisha, 28, from Nur-Sultan'
            },
        },
    },
    'navigation_links': {
        'quickLinks': [
            {'href': '/about', 'ru': 'О нас', 'kz': 'Біз туралы', 'en': 'About Us'},
            {'href': '/reports', 'ru': 'Отчеты', 'kz': 'Есептер', 'en': 'Reports'},
            {'href': '/contact', 'ru': 'Контакты',
                'kz': 'Байланыстар', 'en': 'Contact'},
            {'href': '#', 'ru': 'Волонтерам',
                'kz': 'Еріктілерге', 'en': 'For Volunteers'},
            {'href': '#', 'ru': 'Организациям',
                'kz': 'Ұйымдарға', 'en': 'For Organizations'},
        ],
        'projects': [
            {'href': '#', 'ru': 'Городское озеленение',
                'kz': 'Қала жасылдандыру', 'en': 'Urban Greening'},
            {'href': '#', 'ru': 'Лесные массивы',
                'kz': 'Орман массиві', 'en': 'Forest Areas'},
            {'href': '#', 'ru': 'Школьные программы',
                'kz': 'Мектеп бағдарламалары', 'en': 'School Programs'},
            {'href': '#', 'ru': 'Павлония', 'kz': 'Павлония', 'en': 'Pawlonia'},
            {'href': '#', 'ru': 'Экотуризм', 'kz': 'Экотуризм', 'en': 'Ecotourism'},
        ]
    },
    'howItWorks': {
        'ru': {
            'title': 'Как это работает?',
            'steps': [
                {'number': 1, 'title': 'Выберите количество деревьев', 'subtitle': 'и дизайн сертификата',
                 'description': 'Посадим для вас одно дерево или целый лес. Мы подготовили множество вариантов дизайна сертификата.'},
                {'number': 2, 'title': 'Оплатите посадку деревьев.', 'subtitle': 'Выбор делаете вы сами!',
                 'description': '1 дерево — 500 тенге. Ваш выбор регулярных платежей поможет нам планировать посадки заранее.'},
                {'number': 3, 'title': 'Получите сертификат', 'subtitle': '',
                 'description': 'Подтверждает ваш вклад в восстановление лесов. Сделайте сертификат для себя, для своей организации или в подарок друзьям и близким.'},
                {'number': 4, 'title': 'Получите фотоотчет', 'subtitle': 'и GPS-координаты',
                 'description': 'После фактической посадки вы получите фото и GPS-координаты нового леса. Поделитесь этой радостью!'}
            ]
        },
        'kz': {
            'title': 'Бұл қалай жұмыс істейді?',
            'steps': [
                {'number': 1, 'title': 'Ағаш санын таңдаңыз', 'subtitle': 'және сертификат дизайнын',
                 'description': 'Сіз үшін бір ағашты немесе бүкіл орманды отырғызамыз. Біз сертификат дизайнының көптеген нұсқаларын дайындадық.'},
                {'number': 2, 'title': 'Ағаш отырғызуға төлеңіз.', 'subtitle': 'Таңдауды сіз жасайсыз!',
                 'description': '1 ағаш — 500 теңге. Тұрақты төлемдерді таңдауыңыз бізге алдын ала отырғызуды жоспарлауға көмектеседі.'},
                {'number': 3, 'title': 'Сертификат алыңыз', 'subtitle': '',
                 'description': 'Орман қалпына келтірудегі үлесіңізді растайды. Өзіңіз үшін, ұйымыңыз үшін немесе достарыңыз бен жақындарыңызға сыйлық ретінде сертификат жасаңыз.'},
                {'number': 4, 'title': 'Фото есеп алыңыз', 'subtitle': 'және GPS-координаттар',
                 'description': 'Нақты отырғызғаннан кейін сіз жаңа орманның фотосын және GPS-координаттарын аласыз. Осы қуанышты бөлісіңіз!'}
            ]
        },
        'en': {
            'title': 'How does it work?',
            'steps': [
                {'number': 1, 'title': 'Choose the number of trees', 'subtitle': 'and certificate design',
                 'description': 'We will plant one tree or an entire forest for you. We have prepared many certificate design options.'},
                {'number': 2, 'title': 'Pay for tree planting.', 'subtitle': 'You make the choice!',
                 'description': '1 tree — 500 tenge. Your choice of regular payments will help us plan plantings in advance.'},
                {'number': 3, 'title': 'Get a certificate', 'subtitle': '',
                 'description': 'Confirms your contribution to forest restoration. Make a certificate for yourself, for your organization, or as a gift for friends and family.'},
                {'number': 4, 'title': 'Get a photo report', 'subtitle': 'and GPS coordinates',
                 'description': 'After the actual planting, you will receive photos and GPS coordinates of the new forest. Share this joy!'}
            ]
        }
    },
    'quickDonations': [
        {'amount': 1000, 'trees': 2},
        {'amount': 2500, 'trees': 5},
        {'amount': 5000, 'trees': 10},
        {'amount': 10000, 'trees': 20}
    ],
    'about': {
        'ru': {
            'title': 'О фонде "Наш лес"',
            'mission': 'Наша миссия - восстановление лесных экосистем Казахстана через программы посадки деревьев и экологическое просвещение.',
            'pawloniaTitle': 'Селекция павлонии в Костанайской области',
            'pawloniaDescription': 'Мы разрабатываем программу селекции павлонии - быстрорастущего дерева, которое может значительно ускорить процесс восстановления лесов в нашем регионе.'
        },
        'kz': {
            'title': '"Наш лес" қоры туралы',
            'mission': 'Біздің миссиямыз - ағаш отырғызу бағдарламалары мен экологиялық ағарту арқылы Қазақстанның орман экожүйелерін қалпына келтіру.',
            'pawloniaTitle': 'Қостанай облысындағы павлония селекциясы',
            'pawloniaDescription': 'Біз павлония селекция бағдарламасын дамытып жатырмыз - бұл біздің аймақтағы ормандарды қалпына келтіру процесін айтарлықтай жеделдете алатын жылдам өсетін ағаш.'
        },
        'en': {
            'title': 'About Наш лесFoundation',
            'mission': 'Our mission is to restore Kazakhstan\'s forest ecosystems through tree planting programs and environmental education.',
            'pawloniaTitle': 'Pawlonia selection in Kostanay region',
            'pawloniaDescription': 'We are developing a pawlonia breeding program - a fast-growing tree that can significantly accelerate the forest restoration process in our region.'
        }
    },
    'contact': {
        'email': 'info@greenmile.kz',
        'phone': '+7 (777) 123-45-67',
        'address': 'г. Нур-Султан, ул. Сыганак 10, БЦ "Керуен Сити", офис 205',
        'social': {
            'telegram': '@azamat21x',
            'instagram': '@greenmile.kz',
            'facebook': 'GreenMileKazakhstan'
        }
    },
    'history': {
        'timeline_events': [
            {
                'year': '2010',
                'title_ru': 'Основание',
                'title_kz': 'Құрылуы',
                'title_en': 'Foundation',
                'desc_ru': 'Группа энтузиастов-экологов в Алматы основала "Наш лес" для борьбы с обезлесением.',
                'desc_kz': 'Алматыдағы эколог-энтузиастар тобы ормансызданумен күресу үшін "Наш лес" құрды.',
                'desc_en': 'A group of ecology enthusiasts in Almaty founded "Green Mile" to combat deforestation.',
                'image': 'img/history/foundation.png'
            },
            {
                'year': '2011',
                'title_ru': 'Первая посадка',
                'title_kz': 'Алғашқы отырғызу',
                'title_en': 'First Planting',
                'desc_ru': 'Посажено 1,000 деревьев в первом мероприятии по восстановлению леса в предгорьях Заилийского Алатау.',
                'desc_kz': 'Іле Алатауының баурайында орманды қалпына келтірудің алғашқы іс-шарасында 1,000 ағаш отырғызылды.',
                'desc_en': 'Planted 1,000 trees in the first forest restoration event in the foothills of Zailiysky Alatau.',
                'image': 'img/history/first_planting.png'
            },
            {
                'year': '2015',
                'title_ru': 'Партнерство с правительством',
                'title_kz': 'Үкіметпен серіктестік',
                'title_en': 'Government Partnership',
                'desc_ru': 'Заключено партнерство с Министерством экологии для реализации национальных проектов по озеленению.',
                'desc_kz': 'Ұлттық көгалдандыру жобаларын жүзеге асыру үшін Экология министрлігімен серіктестік жасалды.',
                'desc_en': 'Formed partnership with the Ministry of Ecology for national greening projects.',
                'image': 'img/history/partnership.png'
            },
            {
                'year': '2020',
                'title_ru': 'Расширение',
                'title_kz': 'Кеңею',
                'title_en': 'Expansion',
                'desc_ru': 'Расширение деятельности на регионы Караганды и Актобе, посажено более 100,000 деревьев.',
                'desc_kz': 'Қарағанды және Ақтөбе аймақтарына қызметті кеңейту, 100,000-нан астам ағаш отырғызылды.',
                'desc_en': 'Expanded operations to Karaganda and Aktobe regions, planted over 100,000 trees.',
                'image': 'img/history/expansion.png'
            },
            {
                'year': '2025',
                'title_ru': 'Миллион деревьев',
                'title_kz': 'Миллион ағаш',
                'title_en': 'Million Trees',
                'desc_ru': 'Достигнута отметка в 1 миллион посаженных деревьев, получено международное признание от ООН.',
                'desc_kz': '1 миллион отырғызылған ағаш белгісіне жетті, БҰҰ-дан халықаралық тану алынды.',
                'desc_en': 'Reached the milestone of 1 million trees planted, received international recognition from the UN.',
                'image': 'img/history/million_trees.png'
            }
        ],
        'gallery_images': [
            {
                'src': 'img/history/planting_event.png',
                'alt_ru': 'Мероприятие по посадке',
                'alt_kz': 'Отырғызу іс-шарасы',
                'alt_en': 'Planting event'
            },
            {
                'src': 'img/history/team_action.png',
                'alt_ru': 'Команда в действии',
                'alt_kz': 'Команда әрекетте',
                'alt_en': 'Team in action'
            },
            {
                'src': 'img/history/forest_restoration.png',
                'alt_ru': 'Восстановление леса',
                'alt_kz': 'Орманды қалпына келтіру',
                'alt_en': 'Forest restoration'
            }
        ],
        'achievements': [
            {
                'number': '1M+',
                'label_ru': 'Посаженных деревьев',
                'label_kz': 'Отырғызылған ағаштар',
                'label_en': 'Trees Planted',
                'icon': '<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>'
            },
            {
                'number': '10K+',
                'label_ru': 'Волонтеров',
                'label_kz': 'Еріктілер',
                'label_en': 'Volunteers',
                'icon': '<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>'
            },
            {
                'number': '15',
                'label_ru': 'Регионов',
                'label_kz': 'Аймақтар',
                'label_en': 'Regions',
                'icon': '<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path></svg>'
            }
        ]
    },
    'team': {
        'team_members': [
            {
                'name_ru': 'Айша Жумабаева',
                'name_kz': 'Айша Жұмабаева',
                'name_en': 'Aisha Zhumabaeva',
                'role_ru': 'Основатель и директор',
                'role_kz': 'Құрылтайшы және директор',
                'role_en': 'Founder and Director',
                'bio_ru': 'Айша основала "Наш лес" в 2010 году с мечтой о зеленом Казахстане. Ее страсть к экологии вдохновляет тысячи волонтеров.',
                'bio_kz': 'Айша 2010 жылы "Наш лесны" Қазақстанды жасыл ету арманымен құрды. Оның экологияға деген құштарлығы мыңдаған еріктілерді шабыттандырады.',
                'bio_en': 'Aisha founded "Наш лес" in 2010 with a dream of a greener Kazakhstan. Her passion for ecology inspires thousands of volunteers.',
                'photo': 'img/team/man.png'
            },
            {
                'name_ru': 'Ерлан Абдрахманов',
                'name_kz': 'Ерлан Абдрахманов',
                'name_en': 'Yerlan Abdrakhmanov',
                'role_ru': 'Координатор волонтеров',
                'role_kz': 'Еріктілер үйлестірушісі',
                'role_en': 'Volunteer Coordinator',
                'bio_ru': 'Ерлан управляет волонтерскими программами и организует посадочные мероприятия по всему Казахстану.',
                'bio_kz': 'Ерлан еріктілер бағдарламаларын басқарады және бүкіл Қазақстан бойынша отырғызу шараларын ұйымдастырады.',
                'bio_en': 'Yerlan manages volunteer programs and organizes planting events across Kazakhstan.',
                'photo': 'img/team/man.png'
            },
            {
                'name_ru': 'Светлана Ким',
                'name_kz': 'Светлана Ким',
                'name_en': 'Svetlana Kim',
                'role_ru': 'Специалист по павлонии',
                'role_kz': 'Павлония маманы',
                'role_en': 'Paulownia Specialist',
                'bio_ru': 'Светлана руководит программой селекции павлонии, ускоряя восстановление лесов благодаря быстрорастущим деревьям.',
                'bio_kz': 'Светлана павлония селекциясы бағдарламасын басқарады, жылдам өсетін ағаштар арқылы ормандарды қалпына келтіруді жеделдетеді.',
                'bio_en': 'Svetlana leads the paulownia breeding program, accelerating forest restoration with fast-growing trees.',
                'photo': 'img/team/man.png'
            }
        ]
    },
    'faq': {
        'faqs': [
            {
                'question_ru': 'Что такое "Наш лес"?',
                'question_kz': '"Наш лес" дегеніміз не?',
                'question_en': 'What is "Наш лес"?',
                'answer_ru': '"Наш лес" — это экологическое движение, основанное в 2010 году в Алматы, направленное на восстановление лесов Казахстана и борьбу с изменением климата.',
                'answer_kz': '"Наш лес" — 2010 жылы Алматыда құрылған, Қазақстан ормандарын қалпына келтіруге және климаттың өзгеруімен күресуге бағытталған экологиялық қозғалыс.',
                'answer_en': '"Наш лес" is an environmental movement founded in 2010 in Almaty, aimed at restoring Kazakhstan’s forests and combating climate change.'
            },
            {
                'question_ru': 'Как я могу посадить дерево?',
                'question_kz': 'Ағашты қалай отырғызуға болады?',
                'question_en': 'How can I plant a tree?',
                'answer_ru': 'Вы можете выбрать количество деревьев и оплатить их посадку через наш сайт. После этого вы получите сертификат и фотоотчет с GPS-координатами.',
                'answer_kz': 'Сіз біздің веб-сайт арқылы ағаш санын таңдап, оларды отырғызуға төлей аласыз. Осыдан кейін сіз сертификат және GPS координаттары бар фото есеп аласыз.',
                'answer_en': 'You can choose the number of trees and pay for their planting through our website. Afterward, you’ll receive a certificate and a photo report with GPS coordinates.'
            },
            {
                'question_ru': 'Почему вы используете павлонию?',
                'question_kz': 'Неліктен павлонияны қолданасыздар?',
                'question_en': 'Why do you use paulownia?',
                'answer_ru': 'Павлония быстро растет, поглощает CO2 в 10 раз эффективнее других деревьев и устойчива к суровым климатическим условиям Казахстана.',
                'answer_kz': 'Павлония тез өседі, басқа ағаштарға қарағанда CO2-ны 10 есе тиімді сіңіреді және Қазақстанның қатал климаттық жағдайларына төзімді.',
                'answer_en': 'Paulownia grows quickly, absorbs CO2 10 times more effectively than other trees, and is resilient to Kazakhstan’s harsh climate.'
            },
            {
                'question_ru': 'Как стать волонтером?',
                'question_kz': 'Ерікті болу үшін не істеу керек?',
                'question_en': 'How can I become a volunteer?',
                'answer_ru': 'Свяжитесь с нами через страницу контактов, чтобы узнать о возможностях волонтерства и ближайших мероприятиях по посадке деревьев.',
                'answer_kz': 'Ерікті болу мүмкіндіктері және жақын арада өтетін ағаш отырғызу шаралары туралы білу үшін байланыс беті арқылы бізбен хабарласыңыз.',
                'answer_en': 'Contact us through the contact page to learn about volunteer opportunities and upcoming tree-planting events.'
            },
            {
                'question_ru': 'Как обеспечивается уход за посаженными деревьями?',
                'question_kz': 'Отырғызылған ағаштарға қалай күтім жасалады?',
                'question_en': 'How is care provided for the planted trees?',
                'answer_ru': 'Мы сотрудничаем с местными сообществами и экспертами, чтобы обеспечить полив, защиту от вредителей и мониторинг роста деревьев в течение первых лет.',
                'answer_kz': 'Біз жергілікті қауымдастықтармен және сарапшылармен ынтымақтаса отырып, ағаштардың алғашқы жылдарында суару, зиянкестерден қорғау және өсуін бақылауды қамтамасыз етеміз.',
                'answer_en': 'We partner with local communities and experts to ensure watering, pest protection, and growth monitoring for trees during their early years.'
            },
            {
                'question_ru': 'Могу ли я сделать пожертвование от имени организации?',
                'question_kz': 'Ұйым атынан қайырымдылық жасай аламын ба?',
                'question_en': 'Can I make a donation on behalf of an organization?',
                'answer_ru': 'Да, вы можете сделать пожертвование от имени организации через наш сайт, указав название организации в процессе оплаты. Мы предоставим сертификат на имя организации.',
                'answer_kz': 'Иә, сіз біздің веб-сайт арқылы ұйым атынан қайырымдылық жасай аласыз, төлем барысында ұйымның атын көрсете аласыз. Біз ұйым атына сертификат береміз.',
                'answer_en': 'Yes, you can make a donation on behalf of an organization through our website, specifying the organization’s name during payment. We will provide a certificate in the organization’s name.'
            },
            {
                'question_ru': 'Какие регионы охватывает ваша программа посадки деревьев?',
                'question_kz': 'Сіздердің ағаш отырғызу бағдарламаңыз қандай аймақтарды қамтиды?',
                'question_en': 'Which regions does your tree-planting program cover?',
                'answer_ru': 'Наша программа действует в нескольких регионах Казахстана, включая Алматинскую, Костанайскую, Карагандинскую и Акмолинскую области. Планы по расширению охвата продолжаются.',
                'answer_kz': 'Біздің бағдарлама Қазақстанның бірнеше аймақтарында, соның ішінде Алматы, Қостанай, Қарағанды және Ақмола облыстарында жұмыс істейді. Қамту аясын кеңейту жоспарлары жалғасуда.',
                'answer_en': 'Our program operates in several regions of Kazakhstan, including Almaty, Kostanay, Karaganda, and Akmola regions. Plans for further expansion are ongoing.'
            }
        ]
    }
}


class CertificateService:
    """Service for handling certificate operations"""

    @staticmethod
    def generate_certificate_id():
        """Generate unique certificate ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"GM{timestamp}"

    @staticmethod
    def calculate_environmental_impact(tree_count):
        """Calculate environmental impact of planted trees"""
        return {
            'co2_absorption_per_year': tree_count * 22,  # kg CO2 per tree per year
            'oxygen_production_per_year': tree_count * 16,  # kg O2 per tree per year
            'air_for_people': tree_count * 2,  # people supported with clean air
        }

    @staticmethod
    def send_certificate_email(email, certificate_data):
        """Send certificate via email"""
        try:
            subject = f"Наш лесCertificate - {certificate_data['recipientName']}"

            # You would generate the actual PDF certificate here
            # For now, we'll send a confirmation email

            html_message = render_to_string('emails/certificate_confirmation.html', {
                'certificate_data': certificate_data,
                'environmental_impact': CertificateService.calculate_environmental_impact(
                    certificate_data['treeCount']
                )
            })

            send_mail(
                subject=subject,
                message=f"Thank you for supporting forest restoration! Your certificate has been generated.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )

            return True
        except Exception as e:
            logger.error(f"Failed to send certificate email: {e}")
            return False


# Глобальные переменные для бота и нотификатора
telegram_bot = None
telegram_notifier = None


def start_telegram_bot():
    """Start Telegram bot in background thread"""
    global telegram_bot, telegram_notifier

    telegram_bot = TelegramBot(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        admin_password=settings.TELEGRAM_ADMIN_PASSWORD
    )

    telegram_notifier = TelegramNotifier(telegram_bot)

    # Запуск бота в отдельном потоке
    bot_thread = Thread(target=telegram_bot.start_polling, daemon=True)
    bot_thread.start()
    logger.info("Telegram bot started successfully")


# views.py


def create_order(request):
    """Example view that sends Telegram notification"""
    if request.method == 'POST':
        # Ваша логика создания заказа...
        order_data = {
            'orderId': 'GM20241225123000',
            'customerName': request.POST.get('name'),
            'customerEmail': request.POST.get('email'),
            'customerPhone': request.POST.get('phone'),
            'recipientName': request.POST.get('recipient_name'),
            'treeCount': request.POST.get('tree_count'),
            'selectedDesign': request.POST.get('design'),
            'totalAmount': request.POST.get('amount'),
            'currency': request.POST.get('currency', 'KZT'),
            'status': 'completed'
        }

        # Отправка уведомления через бота - используем глобальный notifier
        from .telegram_bot import get_telegram_notifier
        notifier = get_telegram_notifier()
        if notifier:
            notifier.send_order_notification(order_data)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False})


def list_media_files(request):
    media_files = settings.MEDIA_ROOT
    return JsonResponse({'files': media_files})


def get_language(request):
    return request.session.get('language', 'ru')


def set_language(request, lang):
    if lang in ['ru', 'kz', 'en']:
        request.session['language'] = lang
    return redirect(request.META.get('HTTP_REFERER', reverse('main_app:home')))


@csrf_protect
def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        print(
            f"Registration attempt - Name: {name}, Email: {email}, Phone: {phone}")

        # Validation
        if not name or len(name) < 2:
            logger.error(f"Registration failed: Invalid name - {name}")
            return JsonResponse({'success': False, 'message': 'Имя должно содержать минимум 2 символа'})

        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            logger.error(f"Registration failed: Invalid email - {email}")
            return JsonResponse({'success': False, 'message': 'Некорректный email'})

        if User.objects.filter(email=email).exists():
            logger.error(
                f"Registration failed: Email already exists - {email}")
            return JsonResponse({'success': False, 'message': 'Email уже зарегистрирован'})

        if User.objects.filter(username=email).exists():
            logger.error(
                f"Registration failed: Username already exists - {email}")
            return JsonResponse({'success': False, 'message': 'Email уже используется как имя пользователя'})

        if len(password) < 8:
            logger.error(
                f"Registration failed: Password too short - {len(password)} chars")
            return JsonResponse({'success': False, 'message': 'Пароль должен содержать минимум 8 символов'})

        if password != password_confirm:
            logger.error("Registration failed: Passwords do not match")
            return JsonResponse({'success': False, 'message': 'Пароли не совпадают'})

        try:
            # Create user
            user = User.objects.create_user(
                username=email,  # Using email as username
                email=email,
                password=password,
                first_name=name
            )
            user.save()

            # Link any pending certificates to this user
            if phone:
                normalized_phone = normalize_phone_number(phone)
                # Find certificates with this email or phone and link them
                certificates = Certificate.objects.filter(
                    Q(customer_email=email) | Q(customer_phone=phone)
                )
                certificates.update(user=user)
                print(
                    f"Linked {certificates.count()} certificates to user {email}")

            auth_login(request, user)
            logger.info(f"User registered and logged in successfully: {email}")
            return JsonResponse({'success': True, 'message': 'Регистрация успешна! Перенаправление в профиль...'})

        except ValidationError as e:
            logger.error(f"Registration failed: ValidationError - {str(e)}")
            return JsonResponse({'success': False, 'message': f'Ошибка валидации: {str(e)}'})
        except Exception as e:
            logger.error(f"Registration failed: Unexpected error - {str(e)}")
            return JsonResponse({'success': False, 'message': 'Ошибка сервера. Попробуйте позже.'})

    return redirect('main_app:home')


def test(request):

    language = get_language(request)

    if not request.user.is_authenticated:
        logger.info("Unauthenticated user redirected to register")
        return redirect('main_app:register')

    # Validate user data
    if not request.user.first_name or len(request.user.first_name) < 2 or not request.user.email:
        logger.error(
            f"Invalid user data for {request.user.username}: first_name={request.user.first_name}, email={request.user.email}")
        return JsonResponse({'success': False, 'message': 'Недостаточно данных пользователя. Пожалуйста, обновите профиль.'})

    logger.info(f"Rendering profile.html for user: {request.user.username}")
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'contact': site_data.get('contact', {}),
        'navigation_links': site_data.get('navigation_links', {}),
        'user': request.user
    }
    return render(request, 'profile.html', context)


def login(request):
    logger.info("Login view accessed, redirecting to register")
    return redirect('main_app:register')


def logout(request):
    """Log out user and redirect to home"""
    auth_logout(request)
    logger.info("User logged out")
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('main_app:home')


def home(request):
    language = get_language(request)
    context = {
        'language': language,
        'how_it_works': site_data['howItWorks'][language],
        'navigation': site_data['navigation'][language],
        'hero': site_data['hero'][language],
        'importance': site_data["importance"],
        'statistics': site_data['statistics'],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
    }

    # Calculate progress_percentage
    if context['statistics']['targetTrees'] != 0:
        context['progress_percentage'] = (
            context['statistics']['treesPlanted'] / context['statistics']['targetTrees']) * 314
    else:
        context['progress_percentage'] = 0

    if request.method == 'POST':
        amount = request.POST.get('custom_amount')
        try:
            amount = int(amount)
            if amount < 500:
                messages.error(request, 'Minimum amount is 500 tenge')
            else:
                trees = amount // 500
                messages.success(
                    request, f'Thank you for your donation! You planted {trees} trees.')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid amount')

    return render(request, 'home.html', context)


def about(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'about': site_data.get('about', {}).get(language, {}),
        'statistics': site_data['statistics'],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
    }
    return render(request, 'about.html', context)


def reports(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'planting_areas': [
            {
                'id': 1, 'name': 'Костанайская область' if language == 'ru' else 'Қостанай облысы' if language == 'kz' else 'Kostanay Region',
                'trees': 45600, 'area': 120, 'date': '2024-05-15', 'status': 'completed',
                'coordinates': '53.2144, 63.6246', 'image': 'https://images.unsplash.com/photo-1421790500381-fc9b5996f343?q=80&w=987&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
            },
            {
                'id': 2, 'name': 'Акмолинская область' if language == 'ru' else 'Ақмола облысы' if language == 'kz' else 'Akmola Region',
                'trees': 38200, 'area': 95, 'date': '2024-06-10', 'status': 'in_progress',
                'coordinates': '51.1694, 71.4491', 'image': 'https://images.unsplash.com/photo-1538935732373-f7a495fea3f6?q=80&w=2159&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
            },
            {
                'id': 3, 'name': 'Карагандинская область' if language == 'ru' else 'Қарағанды облысы' if language == 'kz' else 'Karaganda Region',
                'trees': 28900, 'area': 75, 'date': '2024-04-20', 'status': 'completed',
                'coordinates': '49.8047, 73.1094', 'image': 'https://images.unsplash.com/photo-1519567770579-c2fc5436bcf9?w=900&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mjh8fHRyZWVzfGVufDB8fDB8fHww'
            },
            {
                'id': 4, 'name': 'Алматинская область' if language == 'ru' else 'Алматы облысы' if language == 'kz' else 'Almaty Region',
                'trees': 43100, 'area': 110, 'date': '2024-07-05', 'status': 'planned',
                'coordinates': '43.2775, 76.8958', 'image': 'https://images.unsplash.com/photo-1635176061729-35ca541a03a1?w=900&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8dHJlZXMlMjBpbiUyMGNpdHl8ZW58MHx8MHx8fDA%3D'
            }
        ],
        'reports': [
            {
                'id': 1, 'title': 'Годовой отчет 2024' if language == 'ru' else '2024 жылдық есеп' if language == 'kz' else 'Annual Report 2024',
                'type': 'annual', 'date': '2024-12-01', 'size': '2.5 MB', 'downloads': 1250
            },
            {
                'id': 2, 'title': 'Финансовый отчет Q3 2024' if language == 'ru' else '2024 жылдың 3-ші тоқсанындағы қаржылық есеп' if language == 'kz' else 'Financial Report Q3 2024',
                'type': 'financial', 'date': '2024-10-15', 'size': '1.8 MB', 'downloads': 890
            },
            {
                'id': 3, 'title': 'Экологический отчет' if language == 'ru' else 'Экологиялық есеп' if language == 'kz' else 'Environmental Report',
                'type': 'environmental', 'date': '2024-09-30', 'size': '3.2 MB', 'downloads': 650
            }
        ],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
    }
    return render(request, 'reports.html', context)


def contact(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'contact': site_data.get('contact', {}),
        'navigation_links': site_data.get('navigation_links', {}),
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject', 'No subject provided')
        message = request.POST.get('message')

        # Validate required fields
        if not name or not email or not message:
            messages.error(
                request,
                site_data['hero'][language].get(
                    'error_required_fields', 'Пожалуйста, заполните все поля'
                )
            )
        else:
            contact_data = {
                'name': name,
                'email': email,
                'subject': subject,
                'message': message,
                'submitted_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            }

            # Send Telegram notification - используем глобальный notifier
            from .telegram_bot import get_telegram_notifier
            notifier = get_telegram_notifier()
            notification_sent = False
            if notifier:
                notification_sent = notifier.send_contact_notification(
                    contact_data)

            if notification_sent:
                messages.success(
                    request,
                    site_data['hero'][language].get(
                        'message_sent', 'Спасибо за Ваше сообщение. В скором времени мы выйдем с Вами на связь'
                    )
                )
            else:
                messages.error(
                    request,
                    site_data['hero'][language].get(
                        'error_sending_message', 'Возникла ошибка. Пожалуйста, повторите еще раз.'
                    )
                )

        # Redirect to avoid form resubmission
        return redirect('main_app:contact')

    return render(request, 'contact.html', context)


def history(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
        'timeline_events': site_data.get('history', {}).get('timeline_events', []),
        'gallery_images': site_data.get('history', {}).get('gallery_images', []),
        'achievements': site_data.get('history', {}).get('achievements', []),
    }
    return render(request, 'about/history.html', context)


def faq(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
        'faqs': site_data.get('faq', {}).get('faqs', []),
    }
    return render(request, 'about/faq.html', context)


def team(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
        'team_members': site_data.get('team', {}).get('team_members', []),
    }
    return render(request, 'about/team.html', context)


DESIGN_CHOICES = [
    ('professional', 'Professional'),
    ('modern', 'Modern'),
    ('elegant', 'Elegant'),
]


def certificate(request):
    language = get_language(request)
    templates = CertificateTemplate.objects.filter(is_active=True)

    import os
    print("=== FILE EXISTENCE CHECK ===")
    for template in templates:
        if template.background_image:
            full_path = os.path.join(
                settings.MEDIA_ROOT, template.background_image.name)
            exists = os.path.exists(full_path)
            print(f"Template: {template.name}")
            print(f"  DB Path: {template.background_image.name}")
            print(f"  Full Path: {full_path}")
            print(f"  Exists: {exists}")
            if not exists:
                # Check if file is in root
                filename = os.path.basename(template.background_image.name)
                root_path = os.path.join(settings.MEDIA_ROOT, filename)
                root_exists = os.path.exists(root_path)
                print(f"  Root Path: {root_path}")
                print(f"  Root Exists: {root_exists}")

    # Group templates by design and ensure we have templates
    templates_by_design = {}
    for design_code, design_name in DESIGN_CHOICES:
        design_templates = templates.filter(
            design=design_code).order_by('variation')
        templates_by_design[design_code] = list(design_templates)

    # Debug: Print template info
    print("=== TEMPLATE DEBUG INFO ===")
    for design, template_list in templates_by_design.items():
        print(f"Design: {design}, Templates: {len(template_list)}")
        for t in template_list:
            print(
                f"  - {t.name}: {t.background_image.url if t.background_image else 'No image'}")

    # Serialize templates for JavaScript
    serialized_templates = {}
    for design, template_list in templates_by_design.items():
        serialized_templates[design] = []
        for t in template_list:
            # Fix the image URL path
            if t.background_image:
                # Check if file exists in the expected path
                import os
                expected_path = os.path.join(
                    settings.MEDIA_ROOT, t.background_image.name)
                actual_filename = os.path.basename(t.background_image.name)

                # If file doesn't exist in certificate_templates but exists in root
                root_path = os.path.join(settings.MEDIA_ROOT, actual_filename)
                if not os.path.exists(expected_path) and os.path.exists(root_path):
                    # Use the root path
                    background_url = f"/media/{actual_filename}"
                else:
                    background_url = t.background_image.url
            else:
                background_url = ''

            template_data = {
                'id': t.id,
                'variation': t.variation,
                'name': t.name or f"{t.get_design_display()} {t.variation}",
                'description': t.description or f"{t.get_design_display()} template",
                'background_image': background_url
            }
            serialized_templates[design].append(template_data)

    # Get default templates for each design
    certificate_templates = {}
    for design_code, design_name in DESIGN_CHOICES:
        try:
            default_template = templates.filter(design=design_code).first()
            certificate_templates[design_code] = default_template
        except Exception as e:
            logger.error(f"Error getting template for {design_code}: {e}")
            certificate_templates[design_code] = None

    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
        'certificate_templates': certificate_templates,
        'templates_by_design_json': json.dumps(serialized_templates),
        'templates_by_design': templates_by_design,  # Add this for template debugging
    }
    return render(request, 'certificate.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def create_certificate(request):
    """Create a new certificate order"""
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['customerName',
                           'customerEmail', 'recipientName', 'treeCount']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }, status=400)

        # Generate certificate ID - use the same format as payment
        certificate_id = f"GM{int(datetime.now().timestamp() * 1000)}"

        # Prepare order data with all necessary fields
        order_data = {
            'orderId': certificate_id,
            'customerName': data.get('customerName'),
            'customerEmail': data.get('customerEmail'),
            'customerPhone': data.get('customerPhone', ''),
            'recipientName': data.get('recipientName'),
            'certificateText': data.get('certificateText', ''),
            'signatureText': data.get('signatureText', ''),
            'treeCount': int(data.get('treeCount', 1)),
            'templateId': data.get('templateId'),
            'selectedDesign': data.get('selectedDesign', 'professional'),
            'currency': data.get('currency', 'KZT'),
            'totalAmount': data.get('totalAmount'),
            'status': 'pending',
            'createdAt': datetime.now().isoformat()
        }

        # Store order data in session with consistent key
        request.session[f'order_{certificate_id}'] = order_data
        request.session.modified = True

        print(f"Order created and stored: order_{certificate_id}")  # Debug

        return JsonResponse({
            'success': True,
            'orderId': certificate_id,
            'message': 'Certificate order created successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error creating certificate: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


# Updated payment_success function in views.py

# Add this enhanced debugging version of payment_success in views.py

@csrf_exempt
@require_http_methods(["POST"])
def payment_success(request):
    """Handle successful payment with FAST authentication and registration"""
    try:
        # Try to get data from both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
            if not data:
                data = request.GET.dict()

        print("=" * 80)
        print("FAST PAYMENT SUCCESS - DEBUG INFO")
        print("=" * 80)

        # Extract data
        order_id = (data.get('orderId') or data.get('order_id') or
                    data.get('invoiceId') or data.get('invoice_id'))
        payment_id = (data.get('paymentId') or data.get('payment_id') or
                      data.get('transactionId') or data.get('transaction_id'))
        customer_email = (data.get('customerEmail') or data.get('customer_email') or
                          data.get('accountId') or data.get('account_id'))
        customer_name = data.get('customerName') or data.get('customer_name')
        customer_phone = data.get(
            'customerPhone') or data.get('customer_phone')
        amount = data.get('amount')
        currency = data.get('currency')

        print(f"Extracted - Order ID: {order_id}")
        print(f"Extracted - Phone: {customer_phone}")
        print(f"Extracted - Email: {customer_email}")
        print(f"Extracted - Name: {customer_name}")
        print(f"User authenticated: {request.user.is_authenticated}")

        # FAST USER AUTHENTICATION - PRIMARY PATH
        user_authenticated = False
        auth_method = None

        # Check if user is already authenticated
        if request.user.is_authenticated:
            user_authenticated = True
            auth_method = 'existing_session'
            print(f"✓ User already authenticated: {request.user.username}")

        # FAST: Quick email lookup for existing users
        elif customer_email:
            try:
                user = User.objects.get(email=customer_email)
                auth_login(request, user)
                user_authenticated = True
                auth_method = 'fast_email'
                print(
                    f"✓ FAST AUTH: Logged in existing user by email: {customer_email}")

                # Link any pending certificates immediately
                link_certificates_to_user(user, customer_phone, customer_email)

            except User.DoesNotExist:
                print(
                    f"➡ No user found with email: {customer_email} - will show registration")

        # FAST: Quick phone lookup
        elif not user_authenticated and customer_phone:
            user = find_user_by_phone(customer_phone)
            if user:
                auth_login(request, user)
                user_authenticated = True
                auth_method = 'fast_phone'
                print(
                    f"✓ FAST AUTH: Logged in existing user by phone: {customer_phone}")

                # Link any pending certificates immediately
                link_certificates_to_user(user, customer_phone, customer_email)

        print(
            f"FAST AUTH RESULT: {user_authenticated} (method: {auth_method})")

        # Retrieve or create order data (simplified)
        order_data = request.session.get(f'order_{order_id}')
        if not order_data:
            # Create minimal order data from payment info
            order_data = {
                'orderId': order_id or f'GM{int(datetime.now().timestamp() * 1000)}',
                'customerName': customer_name or 'Customer',
                'customerEmail': customer_email,
                'customerPhone': customer_phone or '',
                'recipientName': data.get('recipientName', 'Recipient'),
                'certificateText': data.get('certificateText', ''),
                'signatureText': data.get('signatureText', ''),
                'treeCount': int(data.get('treeCount', 10)),
                'selectedDesign': data.get('selectedDesign', 'professional'),
                'totalAmount': amount or '50000',
                'currency': currency or 'KZT',
                'status': 'completed',
                'paymentId': payment_id or f'pay_{order_id}',
                'createdAt': datetime.now().isoformat(),
                'completedAt': datetime.now().isoformat()
            }
            if order_id:
                request.session[f'order_{order_id}'] = order_data

        # Save certificate to database (fast path)
        certificate_saved = False
        try:
            certificate = Certificate.objects.create(
                certificate_id=order_id,
                customer_name=order_data.get('customerName', ''),
                customer_email=order_data.get('customerEmail', ''),
                customer_phone=order_data.get('customerPhone', ''),
                recipient_name=order_data.get('recipientName', ''),
                certificate_text=order_data.get('certificateText', ''),
                signature_text=order_data.get('signatureText', ''),
                tree_count=order_data.get('treeCount', 1),
                design=order_data.get('selectedDesign', 'professional'),
                total_amount=float(order_data.get('totalAmount', 0)),
                currency=order_data.get('currency', 'KZT'),
                payment_id=payment_id or f'pay_{order_id}',
                status='completed',
                completed_at=timezone.now(),
                user=request.user if request.user.is_authenticated else None
            )
            certificate_saved = True
            print(f"✓ Certificate saved to database: {order_id}")

        except Exception as e:
            logger.error(f"Failed to save certificate: {e}")
            certificate_saved = False

        # BACKGROUND PROCESSING - Don't block response
        import threading

        # Send Telegram notification in background
        def send_telegram_async():
            try:
                from .telegram_bot import get_telegram_notifier
                notifier = get_telegram_notifier()
                if notifier:
                    notifier.send_order_notification(order_data)
            except Exception as e:
                logger.error(f"Background Telegram failed: {e}")

        telegram_thread = threading.Thread(target=send_telegram_async)
        telegram_thread.daemon = True
        telegram_thread.start()

        # Send email in background
        def send_email_async():
            try:
                if customer_email:
                    CertificateService.send_certificate_email(
                        customer_email, order_data)
            except Exception as e:
                logger.error(f"Background email failed: {e}")

        email_thread = threading.Thread(target=send_email_async)
        email_thread.daemon = True
        email_thread.start()

        # Update statistics
        site_data['statistics']['treesPlanted'] += order_data['treeCount']
        site_data['statistics']['totalDonations'] += int(
            float(order_data.get('totalAmount', 0)))

        # PREPARE FAST RESPONSE
        response_data = {
            'success': True,
            'certificateId': order_id,
            'environmentalImpact': CertificateService.calculate_environmental_impact(order_data['treeCount']),
            'userAuthenticated': user_authenticated,
            'authMethod': auth_method,
            'certificateSaved': certificate_saved,
            'customerEmail': customer_email,
            'customerName': customer_name,
            'customerPhone': customer_phone
        }

        # FAST REDIRECT LOGIC
        if user_authenticated:
            # User is authenticated - immediate redirect info
            response_data.update({
                'redirectUrl': reverse('main_app:profile'),
                'message': 'Платеж успешен! Перенаправление в профиль...',
                'showRegistration': False,
                'immediateRedirect': True  # Signal for immediate JS redirect
            })
            print("✓ AUTHENTICATED: Immediate redirect to profile")
        else:
            # User needs registration - provide fast registration data
            response_data.update({
                'redirectUrl': reverse('main_app:home'),
                'message': 'Платеж успешен! Быстрая регистрация...',
                'showRegistration': True,
                'immediateRedirect': False,
                'registrationData': {
                    'email': customer_email,
                    'name': customer_name,
                    'phone': customer_phone
                }
            })
            print("➡ NOT AUTHENTICATED: Show fast registration")

        print(f"\nFAST RESPONSE DATA: {response_data}\n")
        print("=" * 80 + "\n")

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        logger.error("JSON decode error in payment success")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error processing payment success: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def quick_register(request):
    """Ultra-fast registration for payment users"""
    try:
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name', '')
        phone = request.POST.get('phone', '')

        # Ultra-fast validation
        if not email or not password:
            return JsonResponse({'success': False, 'message': 'Email and password required'})

        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already registered'})

        # Create user instantly
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name
        )

        # Login immediately
        auth_login(request, user)

        return JsonResponse({
            'success': True,
            'message': 'Registration successful',
            'redirect': reverse('main_app:profile')
        })

    except Exception as e:
        logger.error(f"Quick registration error: {e}")
        return JsonResponse({'success': False, 'message': 'Registration failed'})


def profile(request):
    """User profile with certificates and statistics"""
    language = get_language(request)

    if not request.user.is_authenticated:
        logger.info("Unauthenticated user redirected to register")
        return redirect('main_app:register')

    # Get user's phone number
    user_phone = request.user.username if request.user.username.startswith(
        '+') or request.user.username.replace('+', '').isdigit() else None

    # Get certificates - match by user, email, or phone
    from django.db.models import Q

    query = Q(user=request.user)
    if request.user.email:
        query |= Q(customer_email=request.user.email)
    if user_phone:
        query |= Q(customer_phone=user_phone)

    user_certificates = Certificate.objects.filter(
        query).order_by('-created_at')

    # Link unlinked certificates to this user
    unlinked_certificates = user_certificates.filter(user__isnull=True)
    if unlinked_certificates.exists():
        count = unlinked_certificates.update(user=request.user)
        logger.info(
            f"Linked {count} certificates to user {request.user.username}")

    # Calculate user statistics
    total_trees = sum(cert.tree_count for cert in user_certificates)
    total_donations = sum(float(cert.total_amount)
                          for cert in user_certificates)

    user_stats = {
        'total_trees': total_trees,
        'total_certificates': user_certificates.count(),
        'total_donations': total_donations,
        'joined_days': (timezone.now() - request.user.date_joined).days,
        'tree_progress_percentage': min(100, total_trees),
        'co2_absorption': total_trees * 22,  # kg per year
        'oxygen_production': total_trees * 16,  # kg per year
        'air_quality_impact': total_trees * 2,  # people supported
    }

    # FIX: Handle UserProfile creation safely
    try:
        from .models import UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            # Profile exists, update phone if needed
            if user_phone and not profile.phone_number:
                profile.phone_number = user_phone
                profile.save()
        except UserProfile.DoesNotExist:
            # Profile doesn't exist, create one
            # Check if phone number already exists in another profile
            if user_phone and UserProfile.objects.filter(phone_number=user_phone).exists():
                # Phone exists in another profile, create without phone
                profile = UserProfile.objects.create(
                    user=request.user, phone_number='')
            else:
                # Safe to create with phone
                profile = UserProfile.objects.create(
                    user=request.user,
                    phone_number=user_phone or ''
                )

        # Update statistics if profile exists
        profile.update_statistics()

    except ImportError:
        # UserProfile model doesn't exist, skip
        pass
    except Exception as e:
        logger.error(f"Error handling UserProfile: {e}")
        # Continue without profile to avoid breaking the page

    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'contact': site_data.get('contact', {}),
        'navigation_links': site_data.get('navigation_links', {}),
        'user': request.user,
        'user_phone': user_phone,
        'user_stats': user_stats,
        'user_certificates': [
            {
                'certificate_id': cert.certificate_id,
                'status': cert.status,
                'tree_count': cert.tree_count,
                'created_at': cert.created_at,
                'recipient_name': cert.recipient_name,
                'design': cert.design,
                'total_amount': cert.total_amount,
                'currency': cert.currency,
                'customer_phone': cert.customer_phone,
                'customer_email': cert.customer_email
            }
            for cert in user_certificates
        ],
        'recent_activities': [
            {
                'type': 'certificate',
                'description': f'Создан сертификат на {cert.tree_count} деревьев' if language == 'ru'
                else f'{cert.tree_count} ағашқа сертификат жасалды' if language == 'kz'
                else f'Certificate created for {cert.tree_count} trees',
                'date': cert.created_at,
                'amount': f'+{cert.tree_count} 🌳'
            }
            for cert in user_certificates[:5]
        ]
    }

    return render(request, 'profile.html', context)


def certificate_success(request, certificate_id):
    """Display success page after payment"""
    language = get_language(request)

    # Retrieve order data from session
    order_data = request.session.get(f'order_{certificate_id}', {})

    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'certificate_id': certificate_id,
        'order_data': order_data,
        'environmental_impact': CertificateService.calculate_environmental_impact(
            order_data.get('treeCount', 0)
        ) if order_data else {}
    }
    return render(request, 'certificate_success.html', context)


@require_http_methods(["GET"])
def certificate_status(request, certificate_id):
    """Get certificate status"""
    try:
        # In a real application, you'd query the database
        order_data = request.session.get(f'order_{certificate_id}')

        if not order_data:
            return JsonResponse({
                'success': False,
                'error': 'Certificate not found'
            }, status=404)

        return JsonResponse({
            'success': True,
            'certificate': {
                'id': certificate_id,
                'status': order_data.get('status', 'pending'),
                'recipientName': order_data.get('recipientName'),
                'treeCount': order_data.get('treeCount'),
                'createdAt': order_data.get('createdAt'),
                'completedAt': order_data.get('completedAt'),
                'environmentalImpact': CertificateService.calculate_environmental_impact(
                    order_data.get('treeCount', 0)
                )
            }
        })

    except Exception as e:
        logger.error(f"Error getting certificate status: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


@require_http_methods(["GET"])
def download_certificate(request, certificate_id):
    """Serve certificate PDF for download"""
    try:
        order_data = request.session.get(f'order_{certificate_id}')

        if not order_data:
            return JsonResponse({
                'success': False,
                'error': 'Certificate not found'
            }, status=404)

        # In a real implementation, you'd generate the PDF here
        # For now, we'll just return the certificate data
        return JsonResponse({
            'success': True,
            'certificate': order_data,
            # You can implement this later
            'downloadUrl': f'/api/certificate/{certificate_id}/pdf/'
        })

    except Exception as e:
        logger.error(f"Error downloading certificate: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


def volunteers(request):
    language = get_language(request)
    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
    }

    return render(request, 'volunteers.html', context)


def organizations(request):
    language = get_language(request)
    context = {
        'title': 'Для организаций - Наш лес',
        'description': 'Сотрудничество с организациями по восстановлению лесов Казахстана. Корпоративные посадки, сертификаты, углеродная нейтральность.',
        'keywords': 'организации, корпоративные посадки, сертификаты, углеродный след, экология Казахстан',
        'language': language,
        'navigation': site_data['navigation'][language],
        'contact': site_data.get('contact', {}),
        'navigation_links': site_data.get('navigation_links', {}),
        'user': request.user
    }
    return render(request, "organizations.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def volunteer_submit(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    # ---- SAVE TO DB -------------------------------------------------
    app = VolunteerApplication(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone', ''),
        region=data.get('region'),
        dates=','.join(data.get('dates', [])),
        experience=data.get('experience', '')
    )
    app.save()

    # ---- SEND TO TELEGRAM -------------------------------------------
    tg_data = {
        **data,
        'dates': ','.join(data.get('dates', [])),
        'submitted': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

    # Используем глобальный notifier вместо создания нового
    from .telegram_bot import get_telegram_notifier
    notifier = get_telegram_notifier()
    if notifier:
        notifier.send_volunteer_notification(tg_data)

    return JsonResponse({"success": True})


@csrf_exempt
@require_http_methods(["POST"])
def organizer_submit(request):
    try:
        data = json.loads(request.body)

        # Сохраняем в БД
        app = OrganizerApplication(
            name=data.get('name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            organization=data.get('organization', ''),
            region=data.get('region', 'Казахстан'),
            plan=data.get('plan', '')
        )
        app.save()

        # Отправляем в Telegram
        tg_data = {
            **data,
            'submitted': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        # Используем глобальный notifier вместо создания нового
        from .telegram_bot import get_telegram_notifier
        notifier = get_telegram_notifier()
        if notifier:
            notifier.send_organizer_notification(tg_data)

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"Error in organizer_submit: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generate_certificate_pdf(request, certificate_id):
    """Generate certificate PDF for download"""
    try:
        # Get certificate data from session
        order_data = request.session.get(f'order_{certificate_id}')

        if not order_data:
            # Try to get from database if user is authenticated
            if request.user.is_authenticated:
                try:
                    from .models import Certificate
                    certificate = Certificate.objects.get(
                        certificate_id=certificate_id,
                        user=request.user
                    )
                    order_data = {
                        'certificateId': certificate.certificate_id,
                        'orderId': certificate.certificate_id,
                        'recipientName': certificate.recipient_name,
                        'certificateText': certificate.certificate_text,
                        'signatureText': certificate.signature_text,
                        'treeCount': certificate.tree_count,
                        'selectedDesign': certificate.design,
                        'totalAmount': certificate.total_amount,
                        'currency': certificate.currency,
                        'createdAt': certificate.created_at.isoformat()
                    }
                except Certificate.DoesNotExist:
                    pass

        if not order_data:
            return JsonResponse({
                'success': False,
                'error': 'Certificate not found'
            }, status=404)

        return JsonResponse({
            'success': True,
            'certificateData': order_data
        })

    except Exception as e:
        logger.error(f"Error generating certificate PDF: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


# Add these helper functions to views.py or create a new utils.py file

def normalize_phone_number(phone):
    """
    Fast phone normalization
    """
    if not phone:
        return None

    # Remove all non-digit characters except leading +
    phone = re.sub(r'[\s\-\(\)]', '', phone)

    # Ensure it starts with + for international format
    if not phone.startswith('+'):
        # Assume Kazakhstan number if no country code
        if phone.startswith('7') or phone.startswith('8'):
            phone = '+7' + phone[1:]
        else:
            phone = '+7' + phone

    return phone


def find_user_by_phone(phone):
    """
    Fast phone lookup for authentication
    """
    if not phone:
        return None

    normalized_phone = normalize_phone_number(phone)

    # Try exact match first
    user = User.objects.filter(username=normalized_phone).first()
    if user:
        return user

    # Try partial match (last 10 digits)
    phone_digits = re.sub(r'\D', '', phone)
    if len(phone_digits) >= 10:
        last_10 = phone_digits[-10:]
        user = User.objects.filter(username__icontains=last_10).first()
        if user:
            return user

    # Try UserProfile if exists
    try:
        from .models import UserProfile
        profile = UserProfile.objects.filter(
            Q(phone_number=normalized_phone) |
            Q(phone_number__icontains=phone_digits[-10:])
        ).first()
        if profile:
            return profile.user
    except ImportError:
        pass

    return None


def find_or_create_user_by_phone(phone, email, name):
    """
    Find existing user by phone or create new one
    Returns (user, created) tuple
    """
    normalized_phone = normalize_phone_number(phone)

    # Try to find existing user
    user = find_user_by_phone(normalized_phone)

    if user:
        return user, False

    # Create new user
    import secrets
    import string
    password = ''.join(secrets.choice(
        string.ascii_letters + string.digits) for _ in range(12))

    user = User.objects.create_user(
        username=normalized_phone,
        email=email,
        password=password,
        first_name=name or 'User'
    )

    # Create or update profile if model exists
    try:
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'phone_number': normalized_phone}
        )
    except ImportError:
        pass

    return user, True


def link_certificates_to_user(user, phone, email):
    """
    Fast linking of certificates to user
    """
    from .models import Certificate
    from django.db.models import Q

    try:
        # Find certificates without user that match phone or email
        query = Q(user__isnull=True)
        if email:
            query |= Q(customer_email=email)
        if phone:
            query |= Q(customer_phone=phone)

        certificates = Certificate.objects.filter(query)
        count = certificates.update(user=user)

        if count > 0:
            print(f"✓ Linked {count} certificates to user {user.username}")
            return count
        return 0

    except Exception as e:
        logger.error(f"Error linking certificates: {e}")
        return 0


def send_auth_notification(user, phone, email, password, language='ru'):
    """
    Send authentication notification email with credentials
    """
    from django.core.mail import send_mail
    from django.conf import settings
    import logging

    logger = logging.getLogger(__name__)

    messages = {
        'ru': {
            'subject': 'Добро пожаловать в Наш лес!',
            'body': f'''
Добро пожаловать в Наш лес!

Вы были автоматически зарегистрированы после успешного пожертвования.

Ваши данные для входа:
Телефон: {phone}
Email: {email}
Пароль: {password}

Вы можете войти в систему используя номер телефона или email.

Рекомендуем сменить пароль после первого входа в личном кабинете.

Спасибо за ваш вклад в озеленение Казахстана!

С уважением,
Команда Наш лес
            '''
        },
        'kz': {
            'subject': 'Наш лесқа қош келдіңіз!',
            'body': f'''
Наш лесқа қош келдіңіз!

Сіз сәтті қайырымдылықтан кейін автоматты түрде тіркелдіңіз.

Кіру деректеріңіз:
Телефон: {phone}
Email: {email}
Құпия сөз: {password}

Жүйеге телефон нөміріңізді немесе email арқылы кіре аласыз.

Жеке кабинетке алғаш кіргеннен кейін құпия сөзді өзгертуді ұсынамыз.

Қазақстанды көгалдандыруға қосқан үлесіңіз үшін рахмет!

Құрметпен,
Наш лескомандасы
            '''
        },
        'en': {
            'subject': 'Welcome to Наш лес!',
            'body': f'''
Welcome to Наш лес!

You have been automatically registered after your successful donation.

Your login credentials:
Phone: {phone}
Email: {email}
Password: {password}

You can log in using your phone number or email.

We recommend changing your password after first login in your profile.

Thank you for your contribution to greening Kazakhstan!

Best regards,
Наш лесTeam
            '''
        }
    }

    msg = messages.get(language, messages['en'])

    try:
        send_mail(
            subject=msg['subject'],
            message=msg['body'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True
        )
        logger.info(f"Auth notification sent to {email}")
        return True
    except Exception as e:
        logger.warning(f"Failed to send auth notification: {e}")
        return False


def register_page(request):
    """Standalone registration page"""
    language = get_language(request)

    if request.user.is_authenticated:
        return redirect('main_app:profile')

    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
    }

    return render(request, 'register.html', context)


# Добавьте эти импорты в начало views.py

# Добавьте эти функции в конец views.py


@csrf_protect
@require_http_methods(["POST"])
def change_password(request):
    """Смена пароля с проверкой старого"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Требуется авторизация'})

    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Валидация
        if not all([current_password, new_password, confirm_password]):
            return JsonResponse({'success': False, 'message': 'Все поля обязательны'})

        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Новые пароли не совпадают'})

        if len(new_password) < 8:
            return JsonResponse({'success': False, 'message': 'Пароль должен содержать минимум 8 символов'})

        # Проверка текущего пароля
        if not request.user.check_password(current_password):
            return JsonResponse({'success': False, 'message': 'Текущий пароль неверен'})

        # Смена пароля
        request.user.set_password(new_password)
        request.user.save()

        # Обновление сессии чтобы пользователь не разлогинился
        update_session_auth_hash(request, request.user)

        logger.info(f"Password changed for user: {request.user.email}")
        return JsonResponse({'success': True, 'message': 'Пароль успешно изменен'})

    except Exception as e:
        logger.error(f"Password change error: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка при смене пароля'})


@csrf_protect
@require_http_methods(["POST"])
def change_email(request):
    """Смена email с проверкой уникальности"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Требуется авторизация'})

    try:
        data = json.loads(request.body)
        new_email = data.get('new_email', '').strip().lower()

        # Валидация email
        if not new_email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', new_email):
            return JsonResponse({'success': False, 'message': 'Некорректный email'})

        # Проверка уникальности
        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            return JsonResponse({'success': False, 'message': 'Этот email уже используется'})

        if User.objects.filter(username=new_email).exclude(id=request.user.id).exists():
            return JsonResponse({'success': False, 'message': 'Этот email уже используется как имя пользователя'})

        # Обновление email
        old_email = request.user.email
        request.user.email = new_email
        request.user.username = new_email  # Если используем email как username
        request.user.save()

        logger.info(
            f"Email changed for user {request.user.id}: {old_email} -> {new_email}")
        return JsonResponse({'success': True, 'message': 'Email успешно изменен'})

    except Exception as e:
        logger.error(f"Email change error: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка при смене email'})


@require_http_methods(["GET"])
def get_user_confidential_data(request):
    """Получение конфиденциальных данных пользователя"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Требуется авторизация'})

    try:
        from .models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=request.user)

        data = {
            'success': True,
            'email': profile.get_visible_email(),
            'phone': profile.get_visible_phone(),
            'full_email': request.user.email,  # Полный email только для владельца
            'full_phone': profile.phone_number,  # Полный телефон только для владельца
            'joined_date': request.user.date_joined.strftime('%d.%m.%Y'),
            'last_login': request.user.last_login.strftime('%d.%m.%Y %H:%M') if request.user.last_login else 'Никогда'
        }

        return JsonResponse(data)

    except Exception as e:
        logger.error(f"Error getting user data: {e}")
        return JsonResponse({'success': False, 'message': 'Ошибка получения данных'})


@csrf_exempt
@require_http_methods(["POST"])
def register_api(request):
    """API endpoint for registration (used by navbar modal and fast registration)"""
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')

        print(
            f"API Registration attempt - Name: {name}, Email: {email}, Phone: {phone}")

        # Validation
        if not name or len(name) < 2:
            return JsonResponse({'success': False, 'message': 'Имя должно содержать минимум 2 символа'})

        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return JsonResponse({'success': False, 'message': 'Некорректный email'})

        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email уже зарегистрирован'})

        if User.objects.filter(username=email).exists():
            return JsonResponse({'success': False, 'message': 'Email уже используется как имя пользователя'})

        if len(password) < 8:
            return JsonResponse({'success': False, 'message': 'Пароль должен содержать минимум 8 символов'})

        try:
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )
            user.save()

            # Link any pending certificates to this user
            if phone:
                normalized_phone = normalize_phone_number(phone)
                certificates = Certificate.objects.filter(
                    Q(customer_email=email) | Q(customer_phone=phone)
                )
                certificates.update(user=user)
                print(
                    f"Linked {certificates.count()} certificates to user {email}")

            auth_login(request, user)
            logger.info(f"User registered via API: {email}")
            return JsonResponse({'success': True, 'message': 'Регистрация успешна!'})

        except Exception as e:
            logger.error(f"API Registration failed: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Ошибка сервера. Попробуйте позже.'})

    except Exception as e:
        logger.error(f"API Registration error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Ошибка сервера'})


@csrf_exempt
@require_http_methods(["POST"])
def login_api(request):
    """API endpoint for login"""
    try:
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        print(f"Login attempt for: {email}")

        if not email or not password:
            return JsonResponse({'success': False, 'message': 'Email и пароль обязательны'})

        # Try to authenticate user
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            logger.info(f"User logged in: {email}")
            return JsonResponse({'success': True, 'message': 'Вход успешен!', 'redirect': reverse('main_app:profile')})
        else:
            return JsonResponse({'success': False, 'message': 'Неверный email или пароль'})

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Ошибка сервера'})
