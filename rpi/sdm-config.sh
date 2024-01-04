#!/bin/bash

sudo sdm \
	--customize $1 \
	--logwidth 132 \
	--extend --xmb 2048 \
	--host batbot \
	--apt-dist-upgrade \
	--cscript sdm-customphase.sh \
	--plugin user:"deluser=pi" \
	--plugin user:"addgroup=sftp" \
	--plugin user:"addgroup=batrun" \
	--plugin user:"adduser=batbot|password=batbot2023|groupadd=batrun" \
	--plugin user:"adduser=sftp_batbot|password=batbot2023|groupadd=batrun,sftp" \
	--plugin network:"netman=nm|nmconn=basic_conn.nmconnection" \
	--plugin L10n:host \
	--plugin apps:"apps=@sdm-apps.txt|name=apps" \
	--plugin raspiconfig:"spi=1|serial=1|net_names=1|rgpio=1" \
	--reboot 20
