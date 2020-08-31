FILES=('messageApi/api.py' 'messageApi/sqlcommands.py' 'sendframe.py' 'chatframe.py' 'constants.py' 'gui.py' 'messageframe.py' 'recipientframe.py' 'responseframe.py' 'updater.py' 'verticalscrolledframe.py')

EXITSTATUS=0
for filename in ${FILES[@]}; do
	pycodestyle $filename
	if [ $? -ne 0 ]; then
		EXITSTATUS=1
	fi
done
echo "Exiting with status " $EXITSTATUS
exit $EXITSTATUS
