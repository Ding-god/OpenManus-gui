    async def _click(self, context: BrowserContext, element_description: str) -> ToolResult:
        """
        简化的点击操作，自动选择最佳策略：
        1. 如果是日期类描述，尝试增强的日期定位策略
        2. 尝试通过 JavaScript 查找包含指定文字的元素
        3. 如果失败，使用视觉模型

        Args:
            context: 浏览器上下文
            element_description: 要点击的元素描述（如"搜索按钮"、"1月30日"）

        Returns:
            ToolResult
        """
        try:
            page = await context.get_current_page()
            await page.bring_to_front()
            await page.wait_for_load_state()

            logger.info(f"[click] 尝试点击: '{element_description}'")

            # 检查是否是日期类描述 - 纯数字或包含"日"、"月"
            is_date_like = (
                element_description.isdigit() or
                re.search(r'^\d+[日号]?$', element_description) or
                re.search(r'\d+月\d+[日号]?', element_description) or
                "日历" in element_description or
                "calendar" in element_description.lower() or
                "月" in element_description or
                "日" in element_description or
                "date" in element_description.lower()
            )

            if is_date_like:
                logger.info(f"[click] 检测到日期类描述，尝试增强的定位方式")
                
                # 提取数字（用于日期）
                day_matches = re.findall(r'(\d+)', element_description)
                
                # 首先尝试使用 Playwright 定位包含数字的日期元素
                for day_num in reversed(day_matches):  # 从最后的数字开始尝试（通常是日期号）
                    try:
                        # 尝试多种选择器来定位日期元素
                        selectors = [
                            f'text="{day_num}"',
                            f'data-testid=date-{day_num}',
                            f'[data-date="{day_num}"]',
                            f'.date-day:has-text("{day_num}")',
                            f'.date-day:text("{day_num}")',
                            f'div:has-text("{day_num}")',
                            f'span:has-text("{day_num}")',
                            f'td:has-text("{day_num}")'
                        ]
                        
                        for selector in selectors:
                            try:
                                logger.debug(f"[click] 尝试选择器: {selector}")
                                locator = page.locator(selector)
                                count = await locator.count()
                                
                                if count > 0:
                                    # 找到潜在的日期元素，检查是否在日历组件中
                                    for i in range(min(count, 3)):  # 检查前3个匹配项
                                        el = locator.nth(i)
                                        
                                        # 检查元素是否在日历相关的容器中
                                        is_calendar_element = False
                                        try:
                                            # 检查元素是否包含在日历类名的父元素中
                                            parent_class = await page.evaluate("""
                                                (element) => {
                                                    let current = element;
                                                    while (current && current.tagName !== 'BODY') {
                                                        if (current.className && 
                                                            (current.className.includes('calendar') || 
                                                             current.className.includes('date') ||
                                                             current.className.includes('picker') ||
                                                             current.className.includes('dp') ||
                                                             current.className.includes('cal'))) {
                                                            return true;
                                                        }
                                                        current = current.parentElement;
                                                    }
                                                    return false;
                                                }
                                            """, await el.element_handle())
                                            is_calendar_element = parent_class
                                        except:
                                            # 如果无法检查父元素，尝试检查元素本身
                                            try:
                                                class_name = await page.evaluate("element => element.className", await el.element_handle())
                                                is_calendar_element = any(keyword in class_name.lower() for keyword in ['calendar', 'date', 'picker', 'dp', 'cal'])
                                            except:
                                                is_calendar_element = True  # 无法检查时假定为有效
                                        
                                        if is_calendar_element and await el.is_visible():
                                            try:
                                                box = await el.bounding_box()
                                                if box and box['y'] < 800:  # 页面可见区域
                                                    click_x = box['x'] + box['width'] / 2
                                                    click_y = box['y'] + box['height'] / 2
                                                    logger.info(f"[click] 找到日期元素: '{element_description}' 数字'{day_num}' at ({click_x:.0f}, {click_y:.0f})")
                                                    
                                                    # 先滚动到元素
                                                    await el.scroll_into_view_if_needed(timeout=3000)
                                                    await asyncio.sleep(0.5)
                                                    
                                                    # 尝试点击元素
                                                    await el.click(timeout=5000)
                                                    await asyncio.sleep(2)  # 等待日期选择的反应，增加延迟以确保页面响应
                                                    
                                                    # 检查页面是否有变化（比如URL改变或出现新元素）
                                                    try:
                                                        current_url = page.url
                                                        await asyncio.sleep(0.5)
                                                        new_url = page.url
                                                        
                                                        if current_url != new_url:
                                                            logger.info(f"[click] 日期点击成功，URL已改变: {current_url} -> {new_url}")
                                                    except:
                                                        pass  # URL 获取失败时忽略
                                                    
                                                    return ToolResult(
                                                        output=f"[click] Playwright 点击日期元素: {element_description} (数字{day_num}) - 位置({click_x:.0f}, {click_y:.0f})"
                                                    )
                                            except Exception as click_err:
                                                logger.debug(f"[click] 尝试点击元素时失败: {click_err}")
                                                continue
                            except Exception as sel_err:
                                logger.debug(f"[click] 选择器失败 {selector}: {sel_err}")
                                continue
                
                # 如果Playwright方式失败，使用视觉模型作为后备
                logger.info(f"[click] Playwright 日期定位失败，使用视觉模型")
                return await self._execute_vision_action(context, f"点击日历中的{element_description}", "click")

            # 策略1: 使用 Playwright locator 精确查找（优先文字精确匹配）
            try:
                # 尝试精确文字匹配
                locator = page.get_by_text(element_description, exact=True)
                if await locator.count() > 0:
                    # 找到精确匹配，点击第一个可见的
                    for i in range(await locator.count()):
                        el = locator.nth(i)
                        if await el.is_visible():
                            text_content = await el.text_content()
                            box = await el.bounding_box()
                            if box and box['y'] < 600:  # 只点击上半部分页面的元素
                                click_x = box['x'] + box['width'] / 2
                                click_y = box['y'] + box['height'] / 2
                                logger.info(f"[click] 精确匹配: '{element_description}' at ({click_x:.0f}, {click_y:.0f})")
                                await page.mouse.click(click_x, click_y)
                                await asyncio.sleep(0.5)
                                return ToolResult(
                                    output=f"[click] 成功点击: '{element_description}' at ({click_x:.0f}, {click_y:.0f})"
                                )

                # 尝试包含文字匹配（但要求元素文字长度不能太长）
                locator = page.get_by_text(element_description, exact=False)
                if await locator.count() > 0:
                    for i in range(min(await locator.count(), 10)):  # 最多检查10个
                        el = locator.nth(i)
                        if await el.is_visible():
                            text_content = await el.text_content()
                            # 只接受文字长度不超过描述3倍的元素
                            if text_content and len(text_content.strip()) <= len(element_description) * 3:
                                box = await el.bounding_box()
                                if box and box['y'] < 600:
                                    click_x = box['x'] + box['width'] / 2
                                    click_y = box['y'] + box['height'] / 2
                                    logger.info(f"[click] 包含匹配: '{text_content[:30]}' at ({click_x:.0f}, {click_y:.0f})")
                                    await page.mouse.click(click_x, click_y)
                                    await asyncio.sleep(0.5)
                                    return ToolResult(
                                        output=f"[click] 成功点击: '{text_content[:30]}' at ({click_x:.0f}, {click_y:.0f})"
                                    )
            except Exception as e:
                logger.debug(f"[click] Playwright locator 失败: {e}")

            # 策略2: 回退到视觉模型
            logger.info(f"[click] JavaScript 未找到匹配元素，使用视觉模型")
            return await self._execute_vision_action(context, f"点击{element_description}", "click")

        except Exception as e:
            logger.error(f"[click] 点击失败: {e}")
            # 最终回退到视觉模型
            return await self._execute_vision_action(context, f"点击{element_description}", "click")