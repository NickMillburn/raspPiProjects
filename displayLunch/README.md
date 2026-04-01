<h1>displayLunch</h1>

<p>A full-screen terminal sign for the Raspberry Pi. Displays <strong>LUNCH</strong> in large white text on a black background. Supports custom messages.</p>

<hr>

<h2>Dependencies</h2>

<pre><code>sudo apt update
sudo apt install -y python3 python3-tk</code></pre>

<hr>

<h2>Installation</h2>

<pre><code>mkdir -p ~/bin
cp ~/raspPiProjects/displayLunch/lunchDisplay.py ~/bin/lunch_sign.py

echo '#!/usr/bin/env bash
exec /usr/bin/python3 "$HOME/bin/lunch_sign.py" "$@"' > ~/bin/lunch

chmod +x ~/bin/lunch_sign.py
chmod +x ~/bin/lunch

echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc</code></pre>

<hr>

<h2>Usage</h2>

<pre><code>lunch</code></pre>
<p>Displays a full-screen <strong>LUNCH</strong> sign.</p>

<pre><code>lunch "Back at 1:30"</code></pre>
<p>Displays a custom message instead.</p>

<p>Press <kbd>Space</kbd>, <kbd>Q</kbd>, or <kbd>Esc</kbd> to close.</p>
