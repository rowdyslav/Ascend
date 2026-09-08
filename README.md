# ASCEND — MVP

Мобильный трекер здоровья, тренировок и протокола. Бэкенд — FastAPI + MongoDB (Beanie),
фронтенд — Flet. Без авторизации: один пользователь по умолчанию, создаётся при первом старте.

- Фронтенд: https://rowdyslav.github.io/Ascend/
- Бэкенд: https://backend-five-swart-37.vercel.app (Swagger: `/docs`)

## Стек

- Python 3.14, менеджер зависимостей [uv](https://docs.astral.sh/uv/) (локфайлы `uv.lock` закоммичены)
- FastAPI 0.141 + Uvicorn, MongoDB 7 + Beanie 1.30 (Motor)
- Flet 0.86 (веб/PWA), matplotlib для графиков
- Docker Compose: `api` (:8000), `frontend` (:8550), `mongo` (:27017)

## Запуск (Docker Compose)

```bash
docker compose up --build
```

После старта:

- Фронтенд: http://localhost:8550
- API и Swagger: http://localhost:8000/docs
- Healthcheck: http://localhost:8000/health

## Запуск без Docker (разработка)

Бэкенд (нужен MongoDB на localhost:27017):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Фронтенд:

```bash
cd frontend
uv sync
ASCEND_API_URL=http://localhost:8000 PYTHONPATH=. uv run flet run --web --port 8550 app/main.py
```

`ASCEND_API_URL` можно не задавать — тогда фронт будет ходить в прод-бэкенд
(`https://backend-five-swart-37.vercel.app`).

## Сид данных

Сид запускается автоматически при первом старте бэкенда, если база пуста:

- дефолтный пользователь (id задаётся `DEFAULT_USER_ID`, см. `docker-compose.yml`);
- ~20 продуктов с реальными нутриентами (творог, курица, гречка, рис, яйца, банан, овсянка и т.д.);
- 8 препаратов протокола (миноксидил местно и 2.5 мг, тадалафил, дутастерид, омега-3, магний, тестостерон по ср+вс, витамин D3);
- 6 упражнений каталога и 3 шаблонных тренировки (Push/Pull/Legs);
- 1 анализ с 10 маркерами (тестостерон, эстрадиол, ферритин, витамин D и др.).

Повторный сид не запускается: он выполняется только если коллекции пусты.
Чтобы пересоздать данные с нуля:

```bash
docker compose down -v && docker compose up --build
```

## Деплой фронтенда на GitHub Pages

Статический бандл собирается скриптом `frontend/scripts/github-pages-build.sh`.
Он стейджит пакет `app/` + `assets/` во временную папку, генерирует entry-шим
`main.py` и закреплённый `requirements.txt` для Pyodide, затем вызывает
`flet publish` с `--base-url /Ascend/` (репозиторий называется `Ascend`) и
кладут результат в `frontend/dist/`.

Локальная сборка (нужен uv):

```bash
cd frontend
./build.sh            # результат — в frontend/dist/
```

Автодеплой: после push в `main` воркфлоу `.github/workflows/deploy-pages.yml`
синхронизирует зависимости через `uv sync --frozen`, собирает бандл и публикует
его на GitHub Pages. В настройках репозитория один раз выберите
**Settings → Pages → Source → GitHub Actions**. Адрес после деплоя:
`https://rowdyslav.github.io/Ascend/`.

## Деплой бэкенда на Vercel

Бэкенд лежит в `backend/` и деплоится как Vercel-проект (корень проекта — `backend/`).

1. Первый раз: `cd backend && vercel` (Vercel CLI) или импортируйте репозиторий
   через дашборд и укажите **Root Directory = backend**.
2. В **Settings → General → Python Version** выберите **3.14**
   (Vercel поддерживает 3.13/3.14).
3. В **Settings → Environment Variables** добавьте:
   - `MONGODB_URI` — строка подключения к Mongo (Atlas);
   - `MONGODB_DB` — `ascend`;
   - `DEFAULT_USER_ID` — `64b000000000000000000001`.
4. Деплой: `vercel --prod` (или push в `main`, если подключён git-деплой).

Отдельный `vercel.json` для бэкенда не нужен: Vercel сам определяет ASGI-приложение
(`app.main:app`) и за его деплой не требуется дополнительная конфигурация.


## Структура

```
ascend/
├── docker-compose.yml
├── .github/workflows/
│   └── deploy-pages.yml          # CI: сборка и деплой фронта на GitHub Pages
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI + lifespan (init/seed)
│   │   ├── core/                 # config (pydantic-settings), db (beanie init)
│   │   ├── models/               # Beanie-модели: user, day, body_metric, workout,
│   │   │                         #   nutrition (Nutrients embedded), protocol, lab
│   │   ├── schemas/              # Pydantic DTO
│   │   ├── api/routes/           # days, body_metrics, workouts, nutrition,
│   │   │                         #   protocol, lab, analytics
│   │   └── services/             # day completion, nutrient scaling, tonnage/1RM, seed
│   ├── pyproject.toml            # зависимости + uv
│   ├── uv.lock
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── main.py               # Flet entry + bottom navigation
│   │   ├── theme.py              # graphite #14161A + teal #2DD4BF + purple #A78BFA
│   │   ├── api_client.py         # httpx wrapper (ASCEND_API_URL)
│   │   ├── components/           # bottom_nav, circular_progress, card, body_map, charts
│   │   ├── screens/              # today, workouts, nutrition, protocol, analytics
│   │   └── utils/                # async_loader, constants, feedback, logger
│   ├── assets/                   # PWA-ассеты: index.html, manifest.json, icons/
│   ├── scripts/                  # github-pages-build.sh, make_icons.py (ручная утилита)
│   ├── build.sh                  # локальная сборка статики
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile
└── README.md
```

## Функциональность

- **Сегодня** — прогресс дня (кольцо), метрики (вес с Δ, сон, энергия, аппетит,
  настроение, самочувствие — тап открывает нижний лист со слайдером), питание
  (6 прогресс-баров), протокол с быстрой отметкой «✓», ежедневные проверки
  (активность, шаги, подъём, комментарий, стресс) и «Закрыть день» с диалогом
  о незавершённых пунктах.
- **Тренировки** — тренировка дня: добавление упражнений и сетов (вес × повторы,
  RIR, отдых), список сетов с тонажем.
- **Питание** — цели дня по типу дня (training/rest/refeed), раскладка факт/цель/осталось/%,
  5 приёмов пищи, поиск продуктов с пересчётом нутриентов под порцию, вкладки
  «Избранные»/«Недавние», ручное создание продукта, рецепты, копирование приёмов
  с произвольной даты, графики ккал/Б/Ж/У за 7/30/90 дней.
- **Протокол** — препараты по времени суток, быстрая отметка, форма приёма
  (доза + единица, время, для инъекций — зона/сторона/реакция), защита от дублей
  (окно 5 минут), остатки на складе, авто-ротация зон инъекций.
- **Аналитика** — календарь месяца, вес (график + скользящие средние 7/30 дней + Δ),
  тренировки (недельный тоннаж, топ упражнений по 1RM), питание (средние ккал/Б/Ж/У,
  пирог макросов, дни выше лимита), протокол (недельное выполнение, топ пропусков,
  предупреждения об остатках), анализы (маркеры с флагами low/normal/high,
  ручной ввод анализов и маркеров).

## iOS PWA

`frontend/assets/` переопределяет дефолтные файлы flet-web:

- `assets/index.html` — iOS-меты (`viewport-fit=cover`, `apple-mobile-web-app-capable`,
  `status-bar-style: black-translucent`, `theme-color: #0F1115`), тёмный экран загрузки;
- `assets/manifest.json` — ASCEND, standalone, portrait, фон `#0F1115`;
- `assets/icons/*` — иконки 192/512 (включая maskable), apple-touch-icon и
  `favicon.png`. Иконки закоммичены в git; регенерировать их нужно только при
  смене логотипа: `python frontend/scripts/make_icons.py` (нужен matplotlib).

Установка на iPhone: Safari → Поделиться → «На экран „Домой"».

## Бизнес-логика (бэкенд)

- Масштабирование нутриентов: `per_100g × (weight_g / 100)` для всех полей, включая микронутриенты.
- Выполнение дня: взвешенная сумма протокол + тренировка + питание + метрики (веса в `core/config.py`).
- Тоннаж: сумма `weight × reps` по рабочим сетам (без разминочных), считается на сервере.
- 1RM (Эпли): `weight × (1 + reps / 30)`.
- Ротация инъекций: зона с самой старой датой последнего использования.
- Защита от дублей: доза того же препарата в пределах ±5 минут → 409 с текстом предупреждения.
- Флаг анализа: value < ref_min → low, > ref_max → high, иначе normal (без референсов — None).

## Переменные окружения

| Переменная        | По умолчанию                                    | Назначение                              |
| ----------------- | ----------------------------------------------- | --------------------------------------- |
| `MONGODB_URI`     | `mongodb://localhost:27017`                     | строка подключения MongoDB              |
| `MONGODB_DB`      | `ascend`                                        | имя базы                                |
| `DEFAULT_USER_ID` | `64b000000000000000000001`                      | id дефолтного пользователя              |
| `ASCEND_API_URL`  | `https://backend-five-swart-37.vercel.app`      | адрес API для фронтенда                 |

Цели питания и веса выполнения дня задаются в `backend/app/core/config.py` (`nutrition_goals`, `completion_weights`).
