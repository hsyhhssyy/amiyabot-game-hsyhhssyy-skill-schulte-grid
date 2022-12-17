#!/bin/sh

zip -q -r amiyabot-game-hsyhhssyy-skill-schulte-grid-1.3.zip *
rm -rf ../../amiya-bot-v6/plugins/amiyabot-game-hsyhhssyy-skill-schulte-grid-*
mv amiyabot-game-hsyhhssyy-skill-schulte-grid-*.zip ../../amiya-bot-v6/plugins/
docker restart amiya-bot 