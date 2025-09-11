document.addEventListener('DOMContentLoaded', function() {
    const containers = document.querySelectorAll('.group');
    if (containers.length === 0) {
        console.warn('No video containers found with class "group"');
        return;
    }

    containers.forEach(container => {
        const video = container.querySelector('video');
        const img = container.querySelector('img');
        const playButton = container.querySelector('.play-button');

        if (!video || !img || !playButton) {
            console.warn('Missing video, image, or play-button element in container:', container);
            return;
        }

        container.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            if (video.paused) {
                img.style.opacity = '0';
                video.style.opacity = '1';
                playButton.style.opacity = '0';
                video.play().then(() => {
                    console.log('Video playback started');
                }).catch(error => {
                    console.error('Video playback error:', error);
                    playButton.style.opacity = '1';
                });
            } else {
                video.pause();
                video.currentTime = 0;
                video.style.opacity = '0';
                img.style.opacity = '1';
                playButton.style.opacity = '0';
            }
        });

        container.addEventListener('mouseenter', function() {
            if (video.paused) {
                playButton.style.opacity = '1';
            }
        });

        container.addEventListener('mouseleave', function() {
            if (video.paused) {
                playButton.style.opacity = '0';
            }
        });

        video.addEventListener('ended', function() {
            video.style.opacity = '0';
            img.style.opacity = '1';
            playButton.style.opacity = '0';
        });
    });
});