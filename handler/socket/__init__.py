# -*- coding: utf-8 -*-


"""
    数据格式
        action
            20s - 请求动作
        newTestTask
            i - task_id测试任务编号
            i - v_user虚拟用户数
            i - ramp_up虚拟用户全部唤醒时间
            i - start_type启动类型
            i - stop_type停止类型
            i - if_error出错后续
            i - exc_times执行次数
            q - file_size压缩包大小
            20s - start_time开始时间
            20s - end_time结束时间
        stopTestTask
            i - task_id测试任务编号
"""
# noinspection SpellCheckingInspection
dataFormat = {
    'action': '20s',
    'newTestTask': 'iiiiiiiq20s20s',
    'stopTestTask': 'i'
}