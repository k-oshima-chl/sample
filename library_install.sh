#apt-get updateで、サーバーのパッケージリストを取得する。
#python-devでpythonの標準ライブラリを導入し、python-pipはpythonのパッケージ管理システムを導入
sudo apt-get -y update
sudo apt-get -y install python-dev
sudo apt-get -y install python-pip

#スクレイピングに必要なライブラリであるBeautifulSoupを導入。
#MySQLを使用するためのライブラリ、MySQL-pythonを導入
sudo pip install beautifulsoup4
sudo pip install MySQL-python