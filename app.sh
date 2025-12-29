# 生成迁移文件
DATABASE_URL="mysql+aiomysql://user:123456@18.170.57.90:3306/ais?charset=utf8mb4" \
alembic revision --autogenerate -m "init"

# 应用最新迁移
DATABASE_URL="mysql+aiomysql://user:123456@18.170.57.90:3306/ais?charset=utf8mb4" \
alembic upgrade head

uvicorn app.main:app --reload --host 0.0.0.0 --port 2222 --http h11

