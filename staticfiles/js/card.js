document.addEventListener('DOMContentLoaded', function() {
    // Region data with localized titles and stats
    const regionData = {
        'northern': {
            'ru': {
                'title': 'Северный Казахстан',
                'stats': [
                    'Площадь лесов: 4.2 млн га',
                    'Основные виды: сосна, береза, осина',
                    'Посажено деревьев: 45,000',
                    'Проекты: Восстановление сосновых боров'
                ]
            },
            'kz': {
                'title': 'Солтүстік Қазақстан',
                'stats': [
                    'Орман аумағы: 4.2 млн га',
                    'Негізгі түрлер: қарағай, қайың, өкпе',
                    'Отырғызылған ағаштар: 45,000',
                    'Жобалар: Қарағай ормандарын қалпына келтіру'
                ]
            },
            'en': {
                'title': 'Northern Kazakhstan',
                'stats': [
                    'Forest area: 4.2 million ha',
                    'Main species: pine, birch, aspen',
                    'Trees planted: 45,000',
                    'Projects: Pine forest restoration'
                ]
            },
            'coords': [54.0, 69.0]
        },
        'central': {
            'ru': {
                'title': 'Центральный Казахстан',
                'stats': [
                    'Площадь лесов: 2.8 млн га',
                    'Основные виды: саксаул, тополь',
                    'Посажено деревьев: 32,000',
                    'Проекты: Борьба с опустыниванием'
                ]
            },
            'kz': {
                'title': 'Орталық Қазақстан',
                'stats': [
                    'Орман аумағы: 2.8 млн га',
                    'Негізгі түрлер: сексеуіл, терек',
                    'Отырғызылған ағаштар: 32,000',
                    'Жобалар: Шөлденудің алдын алу'
                ]
            },
            'en': {
                'title': 'Central Kazakhstan',
                'stats': [
                    'Forest area: 2.8 million ha',
                    'Main species: saxaul, poplar',
                    'Trees planted: 32,000',
                    'Projects: Desertification control'
                ]
            },
            'coords': [48.0, 67.0]
        },
        'eastern': {
            'ru': {
                'title': 'Восточный Казахстан',
                'stats': [
                    'Площадь лесов: 5.1 млн га',
                    'Основные виды: лиственница, кедр',
                    'Посажено деревьев: 58,000',
                    'Проекты: Горное лесовосстановление'
                ]
            },
            'kz': {
                'title': 'Шығыс Қазақстан',
                'stats': [
                    'Орман аумағы: 5.1 млн га',
                    'Негізгі түрлер: балқарағай, шырша',
                    'Отырғызылған ағаштар: 58,000',
                    'Жобалар: Таулы ормандарды қалпына келтіру'
                ]
            },
            'en': {
                'title': 'Eastern Kazakhstan',
                'stats': [
                    'Forest area: 5.1 million ha',
                    'Main species: larch, cedar',
                    'Trees planted: 58,000',
                    'Projects: Mountain forest restoration'
                ]
            },
            'coords': [49.0, 78.0]
        },
        'southern': {
            'ru': {
                'title': 'Южный Казахстан',
                'stats': [
                    'Площадь лесов: 3.5 млн га',
                    'Основные виды: орех, яблоня',
                    'Посажено деревьев: 41,000',
                    'Проекты: Фруктовые лесосады'
                ]
            },
            'kz': {
                'title': 'Оңтүстік Қазақстан',
                'stats': [
                    'Орман аумағы: 3.5 млн га',
                    'Негізгі түрлер: жаңғақ, алма',
                    'Отырғызылған ағаштар: 41,000',
                    'Жобалар: Жеміс ормандары'
                ]
            },
            'en': {
                'title': 'Southern Kazakhstan',
                'stats': [
                    'Forest area: 3.5 million ha',
                    'Main species: walnut, apple',
                    'Trees planted: 41,000',
                    'Projects: Fruit forest gardens'
                ]
            },
            'coords': [43.0, 68.0]
        },
        'western': {
            'ru': {
                'title': 'Западный Казахстан',
                'stats': [
                    'Площадь лесов: 2.1 млн га',
                    'Основные виды: саксаул, тамариск',
                    'Посажено деревьев: 28,000',
                    'Проекты: Прикаспийские леса'
                ]
            },
            'kz': {
                'title': 'Батыс Қазақстан',
                'stats': [
                    'Орман аумағы: 2.1 млн га',
                    'Негізгі түрлер: сексеуіл, тамариск',
                    'Отырғызылған ағаштар: 28,000',
                    'Жобалар: Каспий маңы ормандары'
                ]
            },
            'en': {
                'title': 'Western Kazakhstan',
                'stats': [
                    'Forest area: 2.1 million ha',
                    'Main species: saxaul, tamarisk',
                    'Trees planted: 28,000',
                    'Projects: Caspian forests'
                ]
            },
            'coords': [49.0, 50.0]
        }
    };

    // Get language from the map container's data attribute
    const mapContainer = document.querySelector('.map-container');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }
    const language = mapContainer.dataset.language || 'en'; // Fallback to 'en' if undefined

    // Initialize Yandex Map
    ymaps.ready(function() {
        const myMap = new ymaps.Map("yandex-map", {
            center: [48.0, 67.0], // Kazakhstan center coordinates
            zoom: 5,
            controls: ['zoomControl', 'fullscreenControl']
        });

        // Disable map drag on mobile for better usability
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            myMap.behaviors.disable('drag');
        }

        const regionTitle = document.getElementById('region-title');
        const regionStats = document.getElementById('region-stats');
        if (!regionTitle || !regionStats) {
            console.error('Region title or stats element not found');
            return;
        }

        const placemarks = {};

        // Create placemarks for each region
        for (const region in regionData) {
            const data = regionData[region][language];
            if (!data) {
                console.error(`No data for region ${region} in language ${language}`);
                continue;
            }

            placemarks[region] = new ymaps.Placemark(
                regionData[region].coords,
                {
                    hintContent: data.title,
                    balloonContent: `<div><strong>${data.title}</strong><br>${data.stats.join('<br>')}</div>`
                },
                {
                    preset: 'islands#blueDotIcon',
                    iconColor: '#0095b6'
                }
            );

            // Add click event to placemark
            placemarks[region].events.add('click', function() {
                // Update region info panel
                regionTitle.textContent = data.title;
                regionStats.innerHTML = '';
                data.stats.forEach(stat => {
                    const p = document.createElement('p');
                    p.className = 'text-gray-600';
                    p.textContent = stat;
                    regionStats.appendChild(p);
                });

                // Reset other placemarks and highlight the selected one
                for (const key in placemarks) {
                    placemarks[key].options.set('preset', 'islands#blueDotIcon');
                }
                placemarks[region].options.set('preset', 'islands#blueCircleDotIcon');

                // Pan to the region smoothly
                myMap.panTo(regionData[region].coords, {
                    duration: 500
                });
            });

            myMap.geoObjects.add(placemarks[region]);
        }
    });
});