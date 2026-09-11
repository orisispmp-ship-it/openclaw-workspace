import subprocess, sys
r = subprocess.run(['ntn','pages','create'], stdin=open(r'C:\Users\orisi\.openclaw\workspace\kospi_notion.md','rb'), capture_output=True, text=True)
with open(r'C:\Users\orisi\.openclaw\workspace\py_result.txt','w') as f:
    f.write('rc='+str(r.returncode)+'\n')
    f.write(r.stdout[:200]+'\n')
    f.write(r.stderr[:200])
