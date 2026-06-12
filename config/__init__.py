import pymysql

# Django expects mysqlclient; PyMySQL is a pure-Python drop-in (no native build on Railway).
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.install_as_MySQLdb()
