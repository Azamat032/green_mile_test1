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

from .models import CertificateTemplate

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
            'title': 'О фонде "Зеленая миля"',
            'mission': 'Наша миссия - восстановление лесных экосистем Казахстана через программы посадки деревьев и экологическое просвещение.',
            'pawloniaTitle': 'Селекция павлонии в Костанайской области',
            'pawloniaDescription': 'Мы разрабатываем программу селекции павлонии - быстрорастущего дерева, которое может значительно ускорить процесс восстановления лесов в нашем регионе.'
        },
        'kz': {
            'title': '"Жасыл миля" қоры туралы',
            'mission': 'Біздің миссиямыз - ағаш отырғызу бағдарламалары мен экологиялық ағарту арқылы Қазақстанның орман экожүйелерін қалпына келтіру.',
            'pawloniaTitle': 'Қостанай облысындағы павлония селекциясы',
            'pawloniaDescription': 'Біз павлония селекция бағдарламасын дамытып жатырмыз - бұл біздің аймақтағы ормандарды қалпына келтіру процесін айтарлықтай жеделдете алатын жылдам өсетін ағаш.'
        },
        'en': {
            'title': 'About Green Mile Foundation',
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
                'desc_ru': 'Группа энтузиастов-экологов в Алматы основала "Зеленую милю" для борьбы с обезлесением.',
                'desc_kz': 'Алматыдағы эколог-энтузиастар тобы ормансызданумен күресу үшін "Жасыл милю" құрды.',
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
                'bio_ru': 'Айша основала "Зеленую милю" в 2010 году с мечтой о зеленом Казахстане. Ее страсть к экологии вдохновляет тысячи волонтеров.',
                'bio_kz': 'Айша 2010 жылы "Жасыл миляны" Қазақстанды жасыл ету арманымен құрды. Оның экологияға деген құштарлығы мыңдаған еріктілерді шабыттандырады.',
                'bio_en': 'Aisha founded "Green Mile" in 2010 with a dream of a greener Kazakhstan. Her passion for ecology inspires thousands of volunteers.',
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
                'question_ru': 'Что такое "Зеленая миля"?',
                'question_kz': '"Жасыл миля" дегеніміз не?',
                'question_en': 'What is "Green Mile"?',
                'answer_ru': '"Зеленая миля" — это экологическое движение, основанное в 2010 году в Алматы, направленное на восстановление лесов Казахстана и борьбу с изменением климата.',
                'answer_kz': '"Жасыл миля" — 2010 жылы Алматыда құрылған, Қазақстан ормандарын қалпына келтіруге және климаттың өзгеруімен күресуге бағытталған экологиялық қозғалыс.',
                'answer_en': '"Green Mile" is an environmental movement founded in 2010 in Almaty, aimed at restoring Kazakhstan’s forests and combating climate change.'
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


class TelegramNotifier:
    """Telegram notification service for Green Mile orders and contact form submissions"""

    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = "8254680657:AAG4JY-2nUxvnSO1HKLleoJW8673hWHpdfI"
        self.chat_id = "128610465"
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_order_notification(self, order_data):
        """Send order notification to Telegram"""
        try:
            message = self._format_order_message(order_data)
            return self._send_message(message)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    def send_contact_notification(self, contact_data):
        """Send contact form submission notification to Telegram"""
        try:
            message = self._format_contact_message(contact_data)
            return self._send_message(message)
        except Exception as e:
            logger.error(
                f"Failed to send contact form Telegram notification: {e}")
            return False

    def _format_order_message(self, data):
        """Format order data into a Telegram message"""
        status_emoji = "✅" if data.get('status') == 'completed' else "🔄"

        message = f"""
            {status_emoji} <b>New Green Mile Order</b>

            📋 <b>Order Details:</b>
            • Order ID: <code>{data.get('orderId', 'N/A')}</code>
            • Date: <code>{datetime.now().strftime('%Y-%m-%d %H:%M')}</code>

            👤 <b>Customer Information:</b>
            • Name: <code>{data.get('customerName', 'N/A')}</code>
            • Email: <code>{data.get('customerEmail', 'N/A')}</code>
            • Phone: <code>{data.get('customerPhone', 'N/A') or 'Not provided'}</code>

            🎯 <b>Certificate Details:</b>
            • Recipient: <code>{data.get('recipientName', 'N/A')}</code>
            • Trees: <code>{data.get('treeCount', 'N/A')}</code>
            • Design: <code>{data.get('selectedDesign', 'N/A')}</code>
            • Certificate Text: <code>{data.get('certificateText', 'N/A')[:100]}...</code>

            💰 <b>Payment Information:</b>
            • Amount: <code>{data.get('totalAmount', 'N/A')} {data.get('currency', 'KZT')}</code>
            • Payment ID: <code>{data.get('paymentId', 'N/A')}</code>
            • Status: <code>{data.get('status', 'pending').upper()}</code>

            🌱 <b>Environmental Impact:</b>
            • CO2 Absorption: ~<code>{int(data.get('treeCount', 0)) * 22} kg/year</code>
            • Oxygen Production: ~<code>{int(data.get('treeCount', 0)) * 16} kg/year</code>
            """
        return message.strip()

    def _format_contact_message(self, data):
        """Format contact form data into a Telegram message"""
        message = f"""
            📬 <b>New Contact Form Submission</b>

            📋 <b>Details:</b>
            • Name: <code>{data.get('name', 'N/A')}</code>
            • Email: <code>{data.get('email', 'N/A')}</code>
            • Subject: <code>{data.get('subject', 'No subject provided')}</code>
            • Submitted: <code>{data.get('submitted_at', 'N/A')}</code>

            💬 <b>Message:</b>
            <code>{data.get('message', 'N/A')[:200]}{'...' if len(data.get('message', '')) > 200 else ''}</code>
        """
        return message.strip()

    def _send_message(self, message):
        """Send message to Telegram chat"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }

        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            logger.error(f"Telegram API error: {response.text}")
        return response.status_code == 200


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
            subject = f"Green Mile Certificate - {certificate_data['recipientName']}"

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


def list_media_files(request):
    media_files = os.listdir(os.path.join(
        settings.MEDIA_ROOT, 'certificate_templates'))
    return JsonResponse({'files': media_files})


def get_language(request):
    return request.session.get('language', 'ru')


def set_language(request, lang):
    if lang in ['ru', 'kz', 'en']:
        request.session['language'] = lang
    return redirect(request.META.get('HTTP_REFERER', reverse('main_app:home')))


def test(request):
    return render(request, "test.html")


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

            # Send Telegram notification
            telegram_notifier = TelegramNotifier()
            notification_sent = telegram_notifier.send_contact_notification(
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


# views.py
# views.py - Update the certificate function
def certificate(request):
    language = get_language(request)

    # Get all active templates
    templates = CertificateTemplate.objects.filter(is_active=True)

    # Group templates by design
    templates_by_design = {}
    for design_code, design_name in DESIGN_CHOICES:
        design_templates = templates.filter(
            design=design_code).order_by('variation')
        templates_by_design[design_code] = design_templates

    # Serialize templates for JavaScript - FIX THIS PART
    serialized_templates = {}
    for design, template_list in templates_by_design.items():
        serialized_templates[design] = [
            {
                'id': t.id,
                'variation': t.variation,
                'name': t.name,
                'background_image': t.background_image.url if t.background_image and hasattr(t.background_image, 'url') else '',
                'description': t.description
            }
            for t in template_list
        ]

    # Get default templates for each design
    certificate_templates = {}
    for design_code, design_name in DESIGN_CHOICES:
        try:
            default_template = templates.filter(design=design_code).first()
            if default_template:
                certificate_templates[design_code] = default_template
            else:
                # Create a fallback template object
                certificate_templates[design_code] = type('FallbackTemplate', (), {
                    'background_image': None,
                    'design': design_code
                })()
        except Exception as e:
            logger.error(f"Error getting template for {design_code}: {e}")
            certificate_templates[design_code] = type('FallbackTemplate', (), {
                'background_image': None,
                'design': design_code
            })()

    context = {
        'language': language,
        'navigation': site_data['navigation'][language],
        'navigation_links': site_data.get('navigation_links', {}),
        'contact': site_data.get('contact', {}),
        'certificate_templates': certificate_templates,
        'templates_by_design_json': json.dumps(serialized_templates),
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

        # Generate certificate ID
        certificate_id = CertificateService.generate_certificate_id()

        # Prepare order data
        order_data = {
            'orderId': certificate_id,
            'customerName': data.get('customerName'),
            'customerEmail': data.get('customerEmail'),
            'customerPhone': data.get('customerPhone', ''),
            'recipientName': data.get('recipientName'),
            'certificateText': data.get('certificateText', ''),
            'signatureText': data.get('signatureText', ''),
            'treeCount': int(data.get('treeCount', 1)),
            'currency': data.get('currency', 'KZT'),
            'selectedDesign': data.get('selectedDesign', 'professional'),
            'totalAmount': data.get('totalAmount'),
            'status': 'pending',
            'createdAt': datetime.now().isoformat()
        }

        # Store order data in session for payment processing
        request.session[f'order_{certificate_id}'] = order_data

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


@csrf_exempt
@require_http_methods(["POST"])
def payment_success(request):
    """Handle successful payment"""
    try:
        # Try to get data from both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Handle form data or URL parameters
            data = request.POST.dict()
            if not data:
                # Try GET parameters as fallback
                data = request.GET.dict()

        order_id = data.get('orderId') or data.get('order_id')
        payment_id = data.get('paymentId') or data.get(
            'payment_id') or data.get('payment_reference')

        if not order_id:
            logger.error(
                f"Missing order ID in payment success. Data received: {data}")
            return JsonResponse({
                'success': False,
                'error': 'Missing order ID'
            }, status=400)

        # Retrieve order data from session
        order_data = request.session.get(f'order_{order_id}')
        if not order_data:
            logger.error(f"Order not found in session: {order_id}")
            return JsonResponse({
                'success': False,
                'error': 'Order not found'
            }, status=404)

        # Update order with payment information
        order_data.update({
            'paymentId': payment_id,
            'status': 'completed',
            'completedAt': datetime.now().isoformat()
        })

        # Save updated order data back to session
        request.session[f'order_{order_id}'] = order_data
        request.session.modified = True

        # Send Telegram notification
        telegram_notifier = TelegramNotifier()
        notification_sent = telegram_notifier.send_order_notification(
            order_data)

        if not notification_sent:
            logger.warning(
                f"Failed to send Telegram notification for order {order_id}")

        # Send certificate email
        email_sent = CertificateService.send_certificate_email(
            order_data['customerEmail'],
            order_data
        )

        if not email_sent:
            logger.warning(
                f"Failed to send certificate email for order {order_id}")

        # Update statistics
        site_data['statistics']['treesPlanted'] += order_data['treeCount']
        site_data['statistics']['totalDonations'] += int(
            float(order_data.get('totalAmount', 0)))

        # Return success response with redirect URL
        return JsonResponse({
            'success': True,
            'message': 'Payment processed successfully',
            'certificateId': order_id,
            # Add this redirect URL
            'redirectUrl': f'/certificate/success/{order_id}/',
            'environmentalImpact': CertificateService.calculate_environmental_impact(order_data['treeCount'])
        })

    except json.JSONDecodeError:
        logger.error("JSON decode error in payment success")
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Error processing payment success: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)


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
