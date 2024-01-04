#!/bin/bash
#
# Custom phase script for SDM
#
function loadparams() {
    source $SDMPT/etc/sdm/sdm-readparams
}
# $1 is the phase: "0", "1", or "post-install"

#
# Main code for the script
#
phase=$1
pfx="$(basename $0)" 
loadparams

if [ $phase == "0" ]
then

    logtoboth "* $pfx Phase 0"
    
    logtoboth "* $pfx Phase 0 Completed"

elif [ "$phase" == "1" ]
then

    logtoboth "* $pfx Phase 1"
    logfreespace "at start of $pfx Phase 1"

    logfreespace "at end of $pfx Phase 1"
    logtoboth "* $pfx Phase 1 Completed"
else
    #
    # Post-install edits
    #
    logtoboth "* $pfx Custom Phase post-install"
    logfreespace "at start of $pfx Custom Phase post-install"

	# create python virtual environment
	python3 -m venv /home/batbot/pyvenv
	source /home/batbot/pyvenv/bin/activate

	# create alias to venv
	alias py3=/home/batbot/pyvenv/bin/python3

	# install required python modules
	python3 -m pip install matplotlib scipy numpy pyyaml pyserial
	python3 -m pip install pygnssutils gpxpy

	# setup sftp
	echo "Match group sftp" >> /etc/ssh/sshd_config
	echo "ChrootDirectory /home" >> /etc/ssh/sshd_config
	echo "X11Forwarding yes" >> /etc/ssh/sshd_config
	echo "AllowTcpForwarding no" >> /etc/ssh/sshd_config
	echo "ForceCommand internal-sftp" >> /etc/ssh/sshd_config
	systemctl restart ssh

    logfreespace "at end of $pfx Custom Phase post-install"
    logtoboth "* $pfx Custom Phase post-install Completed"
fi
