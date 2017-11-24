#!/bin/bash
#
#  easyview-n-cap.0.9.1 by andlandl (http://wiki.ubuntuusers.de/EasyCAP_DC60_USB_Audio_und_Videograbber/Easycap_Skript)
#  Date: 08.03.2012
#  The first part of the script is based on the test scripts by Mike Thomas coming with the easycap driver source
#  http://sourceforge.net/projects/easycapdc60/, 
#  the second part (recording section) is mainly the same than in the previous version of this script.
#  The ascii artwork is based on a template i found here: http://www.retrojunkie.com/asciiart/electron/tv.txt
#  For more information view
#  http://easycap.blogspot.com
#  Contact: easycapdc60-blogspot@yahoo.de
#-----------------------------------------------------------------------------
#  
#  Basic options
#
#  preselect parameters for viewing/ capturing
#  change these parameters according to your needs
#-----------------------------------------------------------------------------
VERBOSE=1	# if '0', this script does not show messages window and does not ask for norm and input number anymore
NORM="PAL"	# preselect tv norm 'PAL' or 'NTSC'
INPUT_NR=0		# preselect input number of your easycap where video source is plugged in
input_width=720		# preselect width an height of video source (mplayer, vlc, mencoder)
input_height=576	# other possible combinations: 640/480; 320/240 
ASPECT=169			# '169' (16:9) or '43' (4:3); this value affects video playback with mplayer or vlc only!
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
MESSAGE=()
R_MESAGE=()
EXITCODE=0
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  frequency check
#
#  Requires that precisely one EasyCAP is plugged in.
#-----------------------------------------------------------------------------
MANY=`2>/dev/null lsusb -v -d 05e1:0408 | grep tSamFreq | wc -l `
if [ "x" = "x${MANY}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR:  cannot count 05e1:0408 EasyCAPs")
  EXITCODE=1
#  # exit 1
fi
if [ "0" = "${MANY}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR:  No 05e1:0408 EasyCAP found. Is it plugged in? Is it a Syntek?")
  EXITCODE=1
#  # exit 1
fi
if [ "1" != "${MANY}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR:  Too many 05e1:0408 EasyCAPs found:  one at a time, please")
  EXITCODE=1
#  # exit 1
fi

FREQ=""
FREQ=`2>/dev/null lsusb -v -d 05e1:0408 | grep tSamFreq | sed -e "s,^.* ,,"`
if [ "x${FREQ}" = "x8000" ]; then FREQ=32000; fi
if [ "x${FREQ}" = "x48000" ]; then FREQ=48000; fi
if [ "x" = "x${FREQ}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR:  could not identify audio frequency")
  if_audio="no"
  # exit 1
fi
echo "Audio frequency is ${FREQ} Hz"
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#   videodevices check
#-----------------------------------------------------------------------------
declare -i i0
declare -i i1
declare -i i2
declare -i i3
ls /dev/easy* /dev/video* /proc/asound/* >/dev/null 2>/dev/null
DEV_VIDEO=""
DEV_AUDIO=""
i0=0;
while [ -z ${DEV_VIDEO} ]; do
  if [ -c "/dev/easycap${i0}" ]; then
    DEV_VIDEO="/dev/easycap${i0}"; break
  fi
  if [ -h "/dev/easycap${i0}" ]; then
    DEV_VIDEO="/dev/easycap${i0}"; break
  fi
  if [ 8 -eq ${i0} ]; then DEV_VIDEO="NONE"; fi
  i0=$i0+1
done
if [ "NONE" = "${DEV_VIDEO}" ]; then DEV_VIDEO=""; fi
#-----------------------------------------------------------------------------
#  REMOVE THE FOLLOWING SECTION TO PREVENT THIS SCRIPT FROM LOOKING FOR
#  /dev/video* WHENEVER /dev/easycap* CANNOT BE FOUND.
#=============================================================================
i1=0;
while [ -z ${DEV_VIDEO} ]; do
  if [ -c "/dev/video${i1}" ]; then
    DEV_VIDEO="/dev/video${i1}"; i0=${i1}; break
  fi
  if [ 8 -eq ${i1} ]; then DEV_VIDEO="NONE"; fi
  i1=$i1+1
done
if [ "NONE" = "${DEV_VIDEO}" ]; then DEV_VIDEO=""; fi
#=============================================================================
if [ -z ${DEV_VIDEO} ]; then
  MESSAGE=("${MESSAGE[@]}" "\nCannot find /dev/easycap*, /dev/video*")
  EXITCODE=1
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  check for OSS audio devices
#-----------------------------------------------------------------------------
if_audio="yes"
i2=0;
while [ -z ${DEV_AUDIO} ]; do
  if [ -c "/dev/easysnd${i2}" ]; then DEV_AUDIO="/dev/easysnd${i2}"; fi
  if [ 8 -eq ${i2} ]; then DEV_AUDIO="NONE"; fi
  i2=$i2+1
done
AUDIO_TYPE="oss"
if [ "NONE" = "${DEV_AUDIO}" ]; then DEV_AUDIO=""; fi

#if [ -z ${DEV_AUDIO} ]; then
#AUDIO_TYPE=""
#if_audio="no"
# MESSAGE=("${MESSAGE[@]}" "\nCannot find /dev/easysnd*")
#fi

i3=0;
while [ -z ${DEV_AUDIO} ]; do
  if [ -c "/dev/easyoss${i3}" ]; then DEV_AUDIO="/dev/easyoss${i3}"; fi
  if [ 8 -eq ${i3} ]; then DEV_AUDIO="NONE"; fi
  i3=$i3+1
done
AUDIO_TYPE="oss"
if [ "NONE" = "${DEV_AUDIO}" ]; then DEV_AUDIO=""; fi

#if [ -z ${DEV_AUDIO} ]; then
#AUDIO_TYPE=""
#  MESSAGE=("${MESSAGE[@]}" "\nCannot find /dev/easyoss*")
#  if_audio="no"
#fi

if [ -z ${DEV_AUDIO} ]; then
AUDIO_TYPE=""
  MESSAGE=("${MESSAGE[@]}" "\nCannot find OSS sound device")
  if_audio="no"
fi

#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#   check if easycap devices are read/writeable
#-----------------------------------------------------------------------------
if [ -z ${DEV_VIDEO} ]; then
MESSAGE=("${MESSAGE[@]}" "\nNo videodevice!")
EXITCODE=1
elif [ -r ${DEV_VIDEO} ] && [ -w ${DEV_VIDEO} ]; then
MESSAGE=("${MESSAGE[@]}" "\n${DEV_VIDEO} is accessible by user!")
elif [ -e ${DEV_VIDEO} ]; then
zenity --info --text "Cannot access ${DEV_VIDEO}! \nRun 'chmod a+rw	${DEV_VIDEO}'\nas root from the commandline\nor reinstall driver! " --title "Message"
EXITCODE=1
fi

if [ -r ${DEV_AUDIO} ] && [ -w ${DEV_AUDIO} ]; then
MESSAGE=("${MESSAGE[@]}" "\n${DEV_AUDIO} is accessible by user!")
elif [ -e ${DEV_AUDIO} ]; then
zenity --info --text "\n!!! ${DEV_AUDIO} is NOT accessible by user! \nRun 'chmod a+rw ${DEV_AUDIO}'\nas root from the commandline\notherwise you will hear no sound" --title "Message"
MESSAGE=("${MESSAGE[@]}" "\n!!! ${DEV_AUDIO} is NOT accessible by user! \nRun 'chmod a+rw ${DEV_AUDIO}'\nas root from the commandline\notherwise you will hear no sound")
if_audio="no"
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#   check for ALSA audio device
#-----------------------------------------------------------------------------

while [ -z ${DEV_AUDIO} ]; do
AUDIO_TYPE="alsa";
if_audio="yes";
i0=0;
if [ -z "`ls -1 /proc/asound`" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR: empty /proc/asound")
fi
link=`ls -lart /proc/asound | grep "EasyALSA${i0}" - `
if [ -z "${link}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR: missing /proc/asound/EasyALSA${i0}")
fi
hwnr=`echo ${link} | sed -e "s,^.*-> ,,;s,card,," `
card=/proc/asound/`echo ${link} | sed -e "s,^.*-> ,," `
if [ ! -d "${card}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR: absent or bad card:  ${card}")
fi
if [ ! -d "${card}/pcm0c" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR: absent or bad pcm: ${card}/pcm0c")
fi
if [ -z "${hwnr}" ]; then
  MESSAGE=("${MESSAGE[@]}" "\nERROR: absent or bad card number: ${hwnr}")
  if_audio="no" 
  AUDIO_TYPE=""
  MESSAGE=("${MESSAGE[@]}" "\nEasycap ALSA audio is not supported")
fi
DEV_AUDIO="${hwnr},0"
done

#echo "Video device is ${DEV_VIDEO}"
#echo "Audio device is ${DEV_AUDIO}"
#echo "Audio? ${if_audio}"
#echo "Audio system ${AUDIO_TYPE}"
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  find executable programs
#-----------------------------------------------------------------------------
PROG_LIST=( TRUE 	mplayer		#
			FALSE	vlc			#
			FALSE	cheese		#
			FALSE	tvtime		#
			FALSE 	mencoder	#
			FALSE	sox			#
			) 

PROGS=(mplayer vlc cheese tvtime mencoder sox)
i4=0
for P in ${PROGS[@]}; do
			PROG=`which $P`
        	if [ "x" = "x${PROG}" ] || [ ! -x ${PROG} ]; then
  			echo "Cannot find or execute $P.  Is it installed?"
  			MESSAGE=("${MESSAGE[@]}" "\nCannot find or execute $P.  Is it installed?")
			PROG_LIST[$i4]=""
			PROG_LIST[$i4+1]=""
				if [ "${PROG_LIST[11]}" = "" ]; then
  				echo "Sox is needed for sound with tvtime!"
  				MESSAGE=("${MESSAGE[@]}" "\nSox is needed for sound with tvtime!")
  				fi			
			fi
			i4=$i4+2
done
PROG_LIST[10]=""		# sox will not show up on zenity list
PROG_LIST[11]=""		#
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  display messages and exit if something went wrong
#-----------------------------------------------------------------------------
if [ ${EXITCODE} = 1 ]; then
	MESSAGE=("${MESSAGE[@]}" "\nScript will exit")
fi
echo ${MESSAGE[*]}
#########################
if [ ${VERBOSE} = 1 ]; then
zenity --info --text "${MESSAGE[*]}" --title "Messages"
fi

if [ ${EXITCODE} = 1 ]; then
	exit 1
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  create logfile
#-----------------------------------------------------------------------------
LOGFILE="./test`echo "${DEV_VIDEO}" | sed -e "s,/dev/,," - `.log"

echo "Log file is:  ${LOGFILE}"
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  display zenity list to select program
#-----------------------------------------------------------------------------

view_cap=$(zenity --list --width=250 --height=400 --text "  ___________\n |  .-----------. o|\n | |   EASY_| o|\n | |   CAP_  | o|\n |_\`-----------´ _|\n   ´\`          ´\`\\nTv-norm: $NORM  Input-Nr:$INPUT_NR\nVideodevice: $DEV_VIDEO $input_width x $input_height \nAudiodevice: $AUDIO_TYPE $DEV_AUDIO $FREQ Hz\nIs audio on? $if_audio\nLogfile: $LOGFILE " --radiolist --column "Choice" --column "program" ${PROG_LIST[@]}) || exit 0 

# echo $view_cap
#-----------------------------------------------------------------------------

if [ ${VERBOSE} = 1 ]; then
#-----------------------------------------------------------------------------
#  select tv norm
#-----------------------------------------------------------------------------
title="Select tv norm"
NORM=`zenity  --width="300" --height="150" --title="$title" --list --radiolist --column="Click Here" \
	--column="Norm" --column="Description" \
	TRUE "PAL" "PAL Norm" \
	FALSE "NTSC" "NTSC Norm" \
	` || exit 0 
	echo "$NORM chosen as the tv norm."
#-----------------------------------------------------------------------------
#  select input number
#-----------------------------------------------------------------------------
title="Select input NR"
INPUT_NR=`zenity --width="450"  --height="150" --title="$title" --list --radiolist --column="Click Here" \
	--column="Channel" --column="Description" \
	TRUE "0" "CVBS - DC60" \
	FALSE "1" "CVBS1 - 002" \
	FALSE "2" "CVBS2 - 002" \
	FALSE "3" "CVBS3 - 002" \
	FALSE "4" "CVBS4 - 002" \
	FALSE "5" "S-Video - DC60"
	` || exit 0 
# echo "chosen input:$INPUT_NR"
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  mplayer command
#-----------------------------------------------------------------------------
if [ "alsa" = "${AUDIO_TYPE}" ]; then
M_AUDIO="buffersize=16:alsa:amode=1:forcechan=2:audiorate=${FREQ}:adevice=plughw.${DEV_AUDIO}"
elif [ "oss" = "${AUDIO_TYPE}" ]; then
M_AUDIO="adevice=${DEV_AUDIO}"
fi

if [ "$NORM" = "PAL" ]; then
	fps_count=25
else 
	fps_count=30
fi
# echo $M_AUDIO

if [ "mplayer" = "${view_cap}" ]; then

	if [ "$ASPECT" = 169 ]; then
	M_ASPECT="-aspect 1.78"
	elif [ "$ASPECT" = 43 ]; then
	M_ASPECT="-aspect 1"
	else
	M_ASPECT=""
	fi

if [ "$if_audio" = "yes" ]; then	
1>${LOGFILE} 2>&1 \
mplayer tv:// -tv driver=v4l2:norm=${NORM}:width=${input_width}:height=${input_height}:outfmt=uyvy:device=${DEV_VIDEO}:input=${INPUT_NR}:fps=${fps_count}:${M_AUDIO}:forceaudio:immediatemode=0 -hardframedrop ${M_ASPECT} -ao sdl,${AUDIO_TYPE} -msglevel all=9
elif [ "$if_audio" = "no" ]; then
1>${LOGFILE} 2>&1 \
mplayer tv:// -tv driver=v4l2:norm=${NORM}:width=${input_width}:height=${input_height}:outfmt=uyvy:device=${DEV_VIDEO}:input=${INPUT_NR}:fps=${fps_count} -hardframedrop ${M_ASPECT} -msglevel all=9 -nosound
fi
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  vlc command
#-----------------------------------------------------------------------------
if [ "vlc" = "${view_cap}" ]; then

	if [ "alsa" = "${AUDIO_TYPE}" ]; then
	V_AUDIO="//plughw:${DEV_AUDIO}"
	elif [ "oss" = "${AUDIO_TYPE}" ]; then
	V_AUDIO="//${DEV_AUDIO}"
	fi
	
	if [ "$NORM" = "PAL" ]; then
	V_NORM="pal"
	elif [ "$NORM" = "NTSC" ]; then
	V_NORM="ntsc"
	fi
	
	if [ "$ASPECT" = 169 ]; then
	V_ASPECT="--aspect-ratio=16:9"
	elif [ "$ASPECT" = 43 ]; then
	V_ASPECT="--aspect-ratio=4:3"
	else
	V_ASPECT=""
	fi
	
1>${LOGFILE} 2>&1 \
vlc -vvv v4l2://${DEV_VIDEO}:input=${INPUT_NR}:width=$input_width:height=$input_height:norm=${V_NORM} ${V_ASPECT} :input-slave=${AUDIO_TYPE}:${V_AUDIO} --demux rawvideo 
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  tvtime command
#-----------------------------------------------------------------------------
if [ "tvtime" = "${view_cap}" ]; then
	if [ "alsa" = "${AUDIO_TYPE}" ]; then
	T_AUDIO="-t alsa plughw:${DEV_AUDIO} -s2 -c 2 -r ${FREQ} -s2 -t alsa default"
	elif [ "oss" = "${AUDIO_TYPE}" ]; then
	T_AUDIO="-t raw -s2 ${DEV_AUDIO} -c 2 -r ${FREQ} -s2 -t ossdsp /dev/dsp"
	fi
echo $T_AUDIO
1>${LOGFILE} 2>&1 \
>./tvtime.err
(tvtime -d ${DEV_VIDEO} -i 0 -n "${NORM}" 1>/dev/null 2>>./tvtime.err) &
rc=1
while [ 0 -ne ${rc} ];
do
  tvtime-command run_command "(sox -c 2 -r ${FREQ} ${T_AUDIO} 1>/dev/null 2>>./tvtime.err)" 1>/dev/null 2>>./tvtime.err
  rc=$?
  if [ 0 -eq ${rc} ]; then break; fi
  sleep 0.5
done
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  cheese command
#-----------------------------------------------------------------------------
if [ "cheese" = "${view_cap}" ]; then
1>${LOGFILE} 2>&1 \
cheese -d ${DEV_VIDEO} | tee ${LOGFILE}
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  mencoder command - recording section
#-----------------------------------------------------------------------------

if [ "mencoder" = "${view_cap}" ]; then

#Which aspect should have the target file?
title="Chose aspect of your target file!"
aspect_type=`zenity  --width="400" --height="220" --title="$title" --list --radiolist --column="Click Here" \
	--column="choice" --column="source >> target" \
	TRUE "1" "4:3 > 4:3"\
	FALSE "2" "4:3 > scale=16:9" \
	FALSE "3" "4:3 > crop borders=16:9" \
	` || exit 0 

if [ "$aspect_type" = "1" ]; then
	crop_scale="scale=640:480"
elif [ "$aspect_type" = "2" ]; then
	crop_scale="scale=720:406"
elif [ "$aspect_type" = "3" ]; then
	crop_scale="crop=720:406:0:72"
fi	

#when cancel is pressed
if [ "$aspect_type" = "" ]; then
	zenity --error --title="Stop" --text="Script stopped!"
	exit
fi
#################################################################################
#Quality?
title="What quality do you want to record at ?"
qual_type=`zenity  --width="380" --height="380" --title="$title" --list --radiolist --column="Click Here" \
	--column="Record Time" --column="Description" \
	FALSE "500" "Passable Quality"\
	FALSE "900" "OK Quality"\
	FALSE "1100" "VHS Quality"\
	TRUE "1300" "SVHS Quality"\
	FALSE "1500" "VCD Quality"\
	FALSE "1800" "SVCD Quality" \
	FALSE "2000" "Very Good Quality"\
	FALSE "2500" "High Quality" \
	FALSE "3000" "Excellent Quality"\
	` || exit 0 

#when cancel is pressed
if [ "$qual_type" = "" ]; then
	zenity --error --title="Stop" --text="Script stopped!"
	exit
fi

##################################################################################
#How Long?
title="How long do you want to record for ?"
time_type=`zenity  --width="380" --height="500" --title="$title" --list --radiolist --column="Click Here" \
	--column="Record Time" --column="Description" \
	FALSE "00:00:00" "unlimited"\
	TRUE "00:00:30" "30 seconds for testing"\
	FALSE "00:10:00" "0.2 hours"\
	FALSE "00:30:00" "0.5 hours"\
	FALSE "00:45:00" "0.75 hours"\
	FALSE "01:00:00" "1 hour"\
	FALSE "01:15:00" "1.25 hours"\
	FALSE "01:30:00" "1.5 hours" \
	FALSE "01:45:00" "1.75 hours"\
	FALSE "02:00:00" "2 hours" \
	FALSE "02:15:00" "2.25 hours"\
	FALSE "02:30:00" "2.5 hours" \
	FALSE "02:45:00" "2.75 hours"\
	FALSE "03:00:00" "3 hours" \
	FALSE "03:15:00" "3.25 hours" \
	FALSE "03:30:00" "3.5 hours" \
	` || exit 0 

M_TIME="-endpos $time_type"

#when cancel is pressed
if [ "$time_type" = "" ]; then
	zenity --error --title="Stop" --text="Script was terminated!"
	exit
elif [ "$time_type" = "00:00:00" ]; then
	M_TIME=""
fi
#################################################################################
#user must enter a filename
filedate=$(date +%F_%H:%M-%S)
title="Please enter a filename for your recording, no spaces"
file_name=`zenity  --width="480" --height="150" --title="$title" --file-selection --save --confirm-overwrite --filename="easyrecord_$filedate"` || exit 0 

#when cancel is pressed
if [ "$file_name" = "" ]; then
	zenity --error --title="Stop" --text="Script stopped!"
	exit
fi

###########################################################################################
# summary
R_MESSAGE=("${R_MESSAGE[@]}" "\nRecording options:")
R_MESSAGE=("${R_MESSAGE[@]}" "\nRecording audio: $if_audio")
R_MESSAGE=("${R_MESSAGE[@]}" "\nRecording from Input $INPUT_NR - Norm: $NORM $fps_count fps")
R_MESSAGE=("${R_MESSAGE[@]}" "\nCrop and scale options: $crop_scale")
R_MESSAGE=("${R_MESSAGE[@]}" "\nEncoding quality: $qual_type kb/s")
R_MESSAGE=("${R_MESSAGE[@]}" "\nRecording time:$time_type hours")
R_MESSAGE=("${R_MESSAGE[@]}" "\nFile name: $file_name.avi ")

echo ${R_MESSAGE[*]}

if [ ${VERBOSE} = 1 ]; then
zenity --info --text "${R_MESSAGE[*]}" --title "Recording options"
fi
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
#  mencoder line
#-----------------------------------------------------------------------------
if [ "$if_audio" = "yes" ]; then

zenity --info --title="Start recording with audio" --text="Press ok to start recording"

mencoder tv:// -tv driver=v4l2:norm=$NORM:width=$input_width:height=$input_height:outfmt=uyvy:device=${DEV_VIDEO}:input=${INPUT_NR}:fps=$fps_count:${M_AUDIO}:forceaudio:immediatemode=0 -msglevel all=9 -ovc lavc -ffourcc DX50 -lavcopts vcodec=mpeg4:mbd=2:turbo:vbitrate=$qual_type:keyint=15 -vf pp=lb,$crop_scale -oac mp3lame $M_TIME -o $file_name.avi | tee ${LOGFILE} | zenity --progress --pulsate --auto-close --auto-kill --text="Processing Video - length: $time_type hours" 

zenity --info --title="Job complete" --text="The recording is now complete."


elif [ "$if_audio" = "no" ]; then

zenity --info --title="Start recording without audio" --text="Press ok to start recording"
1>${LOGFILE} 2>&1 \
mencoder tv:// -tv driver=v4l2:norm=$NORM:width=$input_width:height=$input_height:outfmt=uyvy:device=${DEV_VIDEO}:input=${INPUT_NR}:fps=$fps_count -msglevel all=9 -nosound -ovc lavc -ffourcc DX50 -lavcopts vcodec=mpeg4:mbd=2:turbo:vbitrate=$qual_type:keyint=15 -vf pp=lb,$crop_scale -endpos $time_type -o $file_name.avi | tee ${LOGFILE} | zenity --progress --pulsate --auto-close --auto-kill --text="Processing Video - length: $time_type hours" 
zenity --info --title="Job complete" --text="The recording is now complete."

fi

fi
exit 1
