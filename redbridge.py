import concurrent.futures
import argparse
import json
import sys
import os
from adb import adb_commands
from adb import sign_cryptography
from slugify import slugify
from functools import partial

def get_dirname_for_addr(addr):
    return slugify(addr)

def get_device_info(args, signer, addr):

    dirname = get_dirname_for_addr(addr)

    try:

        device = adb_commands.AdbCommands()
        device.ConnectDevice(
            port_path=None,
            serial=addr,
            default_timeout_ms=args.timeout,
            rsa_keys=[signer]
        )
        version = device.Shell('cat /proc/version', timeout_ms=args.timeout)

        if args.screenshot or args.getprop:
            outpath = '{}/{}'.format(args.output, dirname)
            os.mkdir(outpath)

        if args.screenshot:
            try:
                device.Shell(
                    'screencap -p /data/local/tmp/screenshot.png',
                    timeout_ms=args.timeout
                )
                device.Pull(
                    '/data/local/tmp/screenshot.png',
                    dest_file='{}/screenshot.png'.format(outpath),
                    timeout_ms=120000
                )
                device.Shell(
                    'rm -rf /data/local/tmp/screenshot.png',
                    timeout_ms=args.timeout
                )
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as e:
                print(e)

        if args.getprop:
            getprop = device.Shell('getprop', timeout_ms=args.timeout)

    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception:
        return None
    
    if args.getprop:
        with open('{}/getprop.txt'.format(outpath), 'w+') as f:
            f.write(getprop)

    return {
        'addr': addr,
        'dirname': dirname,
        'version': version
    }

def parse_args():

    p = argparse.ArgumentParser(description='')
    p.add_argument('-t', '--threads',
        help='maximum number of threads', type=int, default=10
    )
    p.add_argument('-k', '--adbkey',
        help='path to adb key file', type=str, default='~/.android/adbkey'
    )
    p.add_argument('-o', '--output',
        help='output directory name', type=str, default='output'
    )
    p.add_argument('-P', '--getprop',
        help='retrieve and store device information via getprop',
        default=False,
        action='store_true'
    )
    p.add_argument('-S', '--screenshot',
        help='retrieves a screenshot of the device', default=False,
        action='store_true'
    )
    p.add_argument('--timeout',
        help='adb timeout in milisseconds', type=int, default=10000
    )
    return p.parse_args()

def main():

    args = parse_args()

    addrs = []
    for input_line in sys.stdin:
        addrs.append(input_line.rstrip())

    os.mkdir(args.output)

    signer = sign_cryptography.CryptographySigner(
        os.path.expanduser(args.adbkey)
    )

    x_get_device_info = partial(get_device_info, args, signer)

    i = 0
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as x:
        for device_info in x.map(x_get_device_info, addrs):
            i += 1
            print('Progress: {} addresses tried (of {})'.format(i, len(addrs)))
            if device_info != None:
                results.append(device_info)
    print()

    print('Saving results ...')
    with open('{}/results.json'.format(args.output), 'w+') as f:
        f.write(json.dumps(results))
    print('Done.')

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        exit(1)
    except Exception as e:
        raise