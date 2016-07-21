if [[ -n $VIRTUAL_ENV ]]; then
    echo 'Deactivating existing virtualenv first'
    deactivate
fi

need_pip=0

if [[ ! -d venv ]]; then
    virtualenv venv
    need_pip=1
fi

source venv/bin/activate

if [[ $need_pip == 1 ]]; then
    pip install -r requirements.txt
fi

echo 'You are in the right virtualenv'
