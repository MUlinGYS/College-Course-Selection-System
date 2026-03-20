# 毕设校园选课系统：详细工程清单（核心功能版）

> 目标：仅实现“核心功能”，并确保三点必须项齐全：学生课表、教师端选课名单、管理员用户管理 + 选课轮次配置。
>
> 技术栈：后端 `Django + DRF + JWT`，前端 `Vue3 + Vite`，数据库 `MySQL`（当前开发可先用 sqlite），缓存/队列可先不做或仅预留接口逻辑。

---

## 0. 进度标记（当前已完成）
- [x] 初始化并搭建后端骨架（`backend/`：Django+DRF、JWT 路由占位、CORS 配置占位）
- [x] 初始化并搭建前端最小骨架（`frontend/`：`App.vue` 提供 `/api/health/` 探测按钮）
- [x] Django 数据库迁移已执行（`python Django_app.py migrate`）
- [x] 联调健康检查通路验证已通过（`GET /api/health/` 返回 `{"ok": true}`）

---

## 1. 总体架构与目录规划（开始前确认）
- [ ] 明确后端拆分方式（推荐：按域拆 App）
  - [ ] `users`：用户/角色/权限（管理员管理）
  - [ ] `courses`：课程、开课班级、时间地点、容量
  - [ ] `rounds`：学期、选课轮次配置
  - [ ] `enrollments`：选课、退课、选课记录、冲突校验
- [ ] 明确前端页面与角色路由
  - [ ] 登录/个人中心（公共）
  - [ ] 学生端：课程列表、课程详情、选课/退课、我的已选、我的课表
  - [ ] 教师端：我的开课班级、班级选课名单
  - [ ] 管理员端：用户管理、课程管理、开课班级管理、轮次配置、选课记录查询
- [ ] 明确权限模型（推荐 RBAC）
  - [ ] `ROLE_STUDENT`、`ROLE_TEACHER`、`ROLE_ADMIN`
  - [ ] 管理员权限：用户/课程/开课班级/轮次/选课记录查询
  - [ ] 教师权限：查看自己开课的班级名单
  - [ ] 学生权限：浏览/选课/退课/课表/我的已选

---

## 2. 核心页面清单（前端，固定 14 个页面）
> 页面名为可选约定，关键是功能点不漏。
- [ ] 公共（2）
  - [ ] `Login`：登录并保存 token
  - [ ] `Profile`：个人中心/改密（可简化为改密）
- [ ] 学生端（5）
  - [ ] `StuCourseList`：课程/开课班级列表（按学期、课程名、老师筛选，至少展示基础字段）
  - [ ] `StuCourseDetail`：开课班级详情（时间地点/容量/余量）
  - [ ] `StuEnroll`：选课与退课（同一页面展示冲突/满员/轮次关闭原因）
  - [ ] `StuSelected`：我的已选（可退课入口）
  - [ ] `StuTimetable`：我的课表（从已选汇总生成）
- [ ] 教师端（2）
  - [ ] `TeaSections`：我的开课班级列表
  - [ ] `TeaRoster`：班级选课名单（显示学生信息+选课状态）
- [ ] 管理员端（5）
  - [ ] `AdmUsers`：用户管理（学生/教师/管理员的增删改查或至少启用停用）
  - [ ] `AdmCourses`：课程管理（课程名、学分等）
  - [ ] `AdmSections`：开课班级管理（学期、课程、教师、容量、时间地点）
  - [ ] `AdmRounds`：学期&选课轮次配置（必须：时间范围、对象范围、上限）
  - [ ] `AdmEnrollments`：选课记录查询（按轮次/课程/学生筛选）

---

## 3. 核心 API 清单（REST，固定 26 个）
> 说明：以下路径以 `/api/...` 为统一前缀。你可以在论文里把“请求字段/响应字段/错误码”逐条写清楚。

### 3.1 认证与会话（3）
- [ ] `POST /api/auth/login/`
  - req：`username, password`
  - resp：`access_token, refresh_token, user{...}`
- [ ] `POST /api/auth/refresh/`
  - req：`refresh_token`
  - resp：`access_token`
- [ ] `POST /api/auth/logout/`
  - req：可选 `refresh_token`
  - resp：`ok`

### 3.2 当前用户（1）
- [ ] `GET /api/me`
  - resp：`id, username, role, name`（扩展字段按你模型）

### 3.3 用户管理（5，管理员）
- [ ] `GET /api/users?role=&q=&page=`
- [ ] `POST /api/users`
- [ ] `GET /api/users/{id}`
- [ ] `PUT /api/users/{id}`
- [ ] `DELETE /api/users/{id}`

### 3.4 学期与轮次配置（6，必须）
- [ ] `GET /api/terms`
- [ ] `POST /api/terms`
- [ ] `GET /api/terms/{id}`
- [ ] `GET /api/rounds?term_id=`
- [ ] `POST /api/rounds`
- [ ] `PUT /api/rounds/{id}`
  - req 建议字段：`term_id, name, start_at, end_at, target_scope, max_courses, allow_drop, enabled`

### 3.5 课程（4）
- [ ] `GET /api/courses?q=&page=`
- [ ] `POST /api/courses`
- [ ] `PUT /api/courses/{id}`
- [ ] `DELETE /api/courses/{id}`

### 3.6 开课班级/Section（5）
- [ ] `GET /api/sections?term_id=&course_id=&teacher_id=&q=&page=`
- [ ] `POST /api/sections`
- [ ] `GET /api/sections/{id}`
- [ ] `PUT /api/sections/{id}`
- [ ] `DELETE /api/sections/{id}`

### 3.7 选课核心（2）
- [ ] `POST /api/enrollments`
  - req：`round_id, section_id`
  - resp 成功：`enrollment{ id, section_id, status }`
  - resp 失败：`code, message`（如 `ROUND_CLOSED / FULL / TIME_CONFLICT / LIMIT_EXCEEDED / DUPLICATE`）
- [ ] `DELETE /api/enrollments/{id}`
  - resp：`ok`

### 3.8 学生视图（3）
- [ ] `GET /api/my/enrollments?term_id=`
- [ ] `GET /api/my/timetable?term_id=`
- [ ] `GET /api/my/conflicts?term_id=`（若你希望在 UI 单独展示冲突原因，可实现；否则冲突原因只返回在选课接口里）

### 3.9 教师视图（2）
- [ ] `GET /api/teacher/sections?term_id=`
- [ ] `GET /api/teacher/sections/{id}/roster`

### 3.10 管理员选课记录查询（1）
- [ ] `GET /api/enrollments?round_id=&section_id=&student_id=&page=`

---

## 4. 后端落库模型（MySQL，建议 7–8 张表）
> 每张表都要写入论文“字段/含义/类型/约束（外键、唯一性、非空）”。
- [ ] `users`（可基于 Django auth user + 扩展）
- [ ] `student_profile`（学生扩展，可选但建议）
- [ ] `teacher_profile`（教师扩展，可选但建议）
- [ ] `terms`（学期）
- [ ] `rounds`（选课轮次，必须：开始/结束、对象范围、上限、启用状态）
- [ ] `courses`（课程）
- [ ] `sections`（开课班级/选课对象，必须：容量/时间地点/教师/学期）
- [ ] `enrollments`（选课记录，必须：轮次、班级、学生、状态）

---

## 5. 具体实现顺序（避免忘关键依赖）
> 建议按“模型 -> 序列化器 -> 权限 -> 视图 -> 路由 -> 前端页面 -> 联调 -> 测试”的顺序。

### 5.1 创建 App 与模型（第一阶段）
- [ ] `backend/` 创建 Django app：`users/courses/rounds/enrollments`
- [ ] 编写模型（models.py）
- [ ] 配置 `INSTALLED_APPS` 与迁移
- [ ] 执行 `makemigrations` + `migrate`

### 5.2 序列化器（第二阶段）
- [ ] 为每个核心模型写 Serializer
  - [ ] 用户/资料 Serializer
  - [ ] terms Serializer
  - [ ] rounds Serializer
  - [ ] courses Serializer
  - [ ] sections Serializer
  - [ ] enrollments Serializer
- [ ] 明确输入输出字段（请求/响应）

### 5.3 权限与鉴权（第三阶段）
- [ ] JWT 登录/刷新 已存在：确认可用
- [ ] 实现 DRF 权限类（或在 ViewSet 写 `permission_classes`）
- [ ] 实现角色保护
  - [ ] 学生只能访问自身我的信息、允许选课/退课
  - [ ] 教师只能访问自己开课班级的名单
  - [ ] 管理员可访问所有管理接口

### 5.4 核心业务视图（第四阶段）
- [ ] 实现 `POST /api/enrollments`（最关键）
  - [ ] 校验：当前时间是否在 `round.start_at/end_at`
  - [ ] 校验：section 是否属于该轮次可选范围（若你定义了）
  - [ ] 校验：是否重复选课（同一学生同一 section/或同一课程学期限制）
  - [ ] 校验：容量是否满（考虑并发一致性）
  - [ ] 校验：时间冲突（基于 students 已选的 sections 时间段）
  - [ ] 校验：选课门数上限（轮次/学期级别）
- [ ] 实现 `DELETE /api/enrollments/{id}`（退课）
  - [ ] 校验：轮次是否允许退课（allow_drop）
  - [ ] 校验：仅允许退自己的记录
  - [ ] 更新容量/状态

### 5.5 教师端视图（第五阶段）
- [ ] `GET /api/teacher/sections?term_id=`
- [ ] `GET /api/teacher/sections/{id}/roster`

### 5.6 管理员视图（第六阶段）
- [ ] `users` 管理端
- [ ] `courses` 管理端
- [ ] `sections` 管理端
- [ ] `rounds` 管理端（轮次配置必须完整）
- [ ] `enrollments` 查询端

---

## 6. 并发与冲突（你论文的亮点点位）
> 你开题里提到“高并发选课控制模块”，核心实现建议优先可落地方案（不必过度工程化）。
- [ ] 选课接口并发一致性策略先选一种并写明
  - [ ] MySQL 乐观锁（推荐先做，便于毕设讲清）
  - [ ] Redis 分布式锁（如果你后面要扩展才做）
  - [ ] 队列缓冲（可不做，只在接口返回里做“排队状态”）
- [ ] 时间冲突校验必须覆盖
  - [ ] 同一周同一节/时段重叠
  - [ ] 同一教室是否冲突（如果你也要体现教室资源利用，可以加；但核心选课一般只做学生冲突）

---

## 7. 前端实现顺序（与后端联动）
> 先让页面能显示数据，再接入选课/退课，最后做课表。

### 7.1 基础组件与路由
- [ ] Axios 封装（统一 baseURL、token 注入、错误提示）
- [ ] 路由守卫（根据 token 和 role）

### 7.2 学生侧页面
- [ ] `StuCourseList` 接 `GET /api/sections` 或 `GET /api/courses` 聚合展示
- [ ] `StuCourseDetail` 展示 `GET /api/sections/{id}`
- [ ] `StuEnroll` 调 `POST /api/enrollments` 和 `DELETE /api/enrollments/{id}`
- [ ] `StuSelected` 调 `GET /api/my/enrollments`
- [ ] `StuTimetable` 调 `GET /api/my/timetable`

### 7.3 教师侧页面
- [ ] `TeaSections` 调 `GET /api/teacher/sections`
- [ ] `TeaRoster` 调 `GET /api/teacher/sections/{id}/roster`

### 7.4 管理员侧页面
- [ ] `AdmUsers` 调 `users` 管理接口
- [ ] `AdmCourses` 调 `courses` 管理接口
- [ ] `AdmSections` 调 `sections` 管理接口
- [ ] `AdmRounds` 调 `terms/rounds` 管理接口（重点：时间范围、对象范围、上限）
- [ ] `AdmEnrollments` 调 `GET /api/enrollments` 查询

---

## 8. 测试与自检（每阶段都做）
- [ ] 后端：手动调用每个 API（用 Postman 或 curl）
- [ ] 权限：用三个角色分别访问所有页面入口，确保越权报 403
- [ ] 冲突：构造两门课时间重叠，验证选课接口返回 `TIME_CONFLICT`
- [ ] 满员：把容量设为 1，并模拟两次选课（必要时并发测试），验证返回 `FULL`
- [ ] 轮次关闭：修改 `round` 时间，验证选课接口返回 `ROUND_CLOSED`
- [ ] 退课：验证退课后容量可恢复、课表也能刷新

---

## 9. 最终交付清单（论文与演示必须）
- [ ] 论文图表：架构图（前后端分离 + 模块）
- [ ] 论文图表：ER 图（核心表：terms/rounds/courses/sections/enrollments）
- [ ] 论文图表：流程图（选课流程含校验分支）
- [ ] 接口说明表：26 个 API（请求/响应字段+错误码）
- [ ] 页面演示截图：14 个页面按角色展示

