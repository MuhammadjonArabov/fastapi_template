
# FastAPI Temaplte

## Qamrab oladi:

- User Modellar
- Authentication | Authorization
- Unittestlar
- JWT
- PostgresSQL(SQLAlchemy|Alembic)

## Avzalliklari
- Foydalanish uchun qulay
- Tushunishga oson
- Ko'p qamrovli
- Tartibli

## PostgreSQL database yaratish | Docker bilan.
1. Operatsion tizimingizga docker yoki dokcer-desktop daturini o'rnating.
2. Ungi ishga tushurgandan so'ng postgres imagini yuklang.
```bash
docker pull postgres
```
3. Shu postgres imagedan container yarating:
```bash
docker run --name <CONTAINER_NAME> -p 5432:5432 -e POSTGRES_PASSWORD=<PASSWORD> -e POSTGRES_USER=<USER> -d postgres
```
4. Ishga tushgan postgres ichida database yarating(haqiqiy va test uchun):
```bash
docker exec -ti <CONTAINER_NAME> createdb -U <USER> <DB_NAME>

docker exec -ti <CONTAINER_NAME> createdb -U <USER> <TEST_DB_NAME>
```

Agar siz hammasini to'g'ri qilgan bo'lsangiz sizda quyidagi ma'lumotlar bor:
- DB_USER=<USER>
- DP_PASSWORD=<PASSWORD>
- DB_PORT=5432
- DB_NAME=<DB_NAME>
- DB_ADDRESS=localhost
-
- TEST_DB_USER=<USER>
- TEST_DB_PASSWORD=<PASSWORD>
- TEST_DB_PORT=5432
- TEST_DB_NAME=<TEST_DB_NAME>
- TEST_DB_ADDRESS=localhost

Agar iloji bo'lsa postgres uchun userni ham yangi yaratish tafsiya qilinadi.

## Loyihani ishga tushurish:

1. Kerakli papkaga boring va kodni githubdan yuklab oling:
```bash
git clone https://github.com/Abdurasuloff/fastapi-template.git
```

2. Kerakli kutubxonalarni o'rnating:
Buning uchun birinchi vertual muhit yarating:

```bash
# Windows uchun
python -m venv myenv
myenv\Scripts\activate

#Mac OS / Linux uchun
python3 -m venv myenv
source myenv/bin/activate

#Kutubxonalarni o'rnating
pip install -r requirements.txt 
```
3. .env faylini .env.example fayliga qarab kerakli ma'lumotlar bilan to'ldiring
4. Databaseni migrate qiling:
```bash
cd app
alembic upgrade head
```
5. Serverni ishga tushuring:

```bash
fastapi dev
```

## Testlarni ishga tushurish.
1. .env testlar uchun boshqa databaseni ko'rsatgan bo'lishingiz kerak.
2. Test databaseni sozlash uchun:
```bash
cd app
python test_setup.py
```
3. Testlarni ishga tushuring
```bash
pytest
```

## Eslatma
Bu templateni asosiy qismi https://github.com/seapagan/fastapi-template.git ga tegishli. Ushbu template uchun takliflar yoki xatolar bo'lsa bemalol aloqaga chiqing.

Credit: https://github.com/seapagan/fastapi-template.git
