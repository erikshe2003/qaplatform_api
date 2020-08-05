# -*- coding: utf-8 -*-

import flask

import route

import io
from handler.log import api_logger
from flask import Response
import pandas as pd
from io import BytesIO
from model.mysql import model_mysql_casePrecondition
from model.mysql import model_mysql_case
from model.mysql import model_mysql_caseFile
from model.mysql import model_mysql_caseStep
from model.mysql import model_mysql_project
import time

"""
    获取个人测试计划基础信息-api路由
    ----校验
            校验账户是否存在
            校验账户操作令牌
            校验账户所属角色是否有API操作权限
            校验传参
    ----操作
            判断用例是否存在
            返回操作结果
"""


# @route.check_user
# @route.check_token
# @route.check_auth
@route.check_get_parameter(
    ['projectId', int, None, None],
    ['caseList', list, 0, None]

)


def key_caseExporFilet_get():
    # 初始化返回内容

    cases_info=[]
    count=0

    # 取出必传入参
    project_id = flask.request.args['projectId']
    case_list = flask.request.args['caseList']

    cases_id=case_list.split(',')

    #判断项目是否存在，并获取仓库id
    try:
        mysql_project_info = model_mysql_project.query.filter(
            model_mysql_project.id == project_id
        ).first()
    except Exception as e:
        api_logger.error("读取失败，失败原因：" + repr(e))
        return route.error_msgs[500]['msg_db_error']
    else:
        if mysql_project_info is None:
            return route.error_msgs[201]['msg_no_project']



    #判断用例是否存在并生成用例列表

    for id in cases_id:
        ossPaths = ""
        caseSteps = ""
        expectations = ""


        try:
            mysql_cases_info = model_mysql_case.query.filter(
                model_mysql_case.id==int(id),
                model_mysql_case.status == 1,
                model_mysql_case.type == 2,
                model_mysql_case.projectId == project_id
            ).first()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_cases_info is None:
                pass
            else:
                cases_info.append({
                    'id': mysql_cases_info.id,
                    'columnId': None,
                    'title': mysql_cases_info.title,
                    'level': mysql_cases_info.level,
                    'casePrecondition': None,
                    'caseStep': None,
                    'expectation':None,
                    'ossPath': None
                })

        # 判断目录是否存在，获取目录名称
        try:
            mysql_column_info = model_mysql_case.query.filter(
                model_mysql_case.id==mysql_cases_info.columnId,
                model_mysql_case.status == 1,
                model_mysql_case.type == 1,

            ).first()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_column_info is None:
                return route.error_msgs[201]['msg_no_catalogue']
            else:
                cases_info[count]['columnId'] = mysql_column_info.title

        # 查询是否存在前置条件
        try:
            mysql_casePrecondition_info = model_mysql_casePrecondition.query.filter(
                model_mysql_casePrecondition.caseId == id
            ).first()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_casePrecondition_info is None:
                pass
            else:
                cases_info[count]['casePrecondition']= mysql_casePrecondition_info.content


        # 查询是否存在附件
        try:
            mysql_caseFile_info = model_mysql_caseFile.query.filter(
                model_mysql_caseFile.caseId == id, model_mysql_caseFile.status == 1
            ).all()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_caseFile_info is None:
                pass
            else:
                for xx in mysql_caseFile_info:
                    ossPaths=ossPaths+'\n'+xx.ossPath
                cases_info[count]['ossPath'] = ossPaths

        # 查询是否存在测试步骤
        try:
            mysql_caseStep_info = model_mysql_caseStep.query.filter(
                model_mysql_caseStep.caseId == id,model_mysql_caseStep.status==1
            ).order_by(model_mysql_caseStep.index).all()
        except Exception as e:
            api_logger.error("读取失败，失败原因：" + repr(e))
            return route.error_msgs[500]['msg_db_error']
        else:
            if mysql_caseStep_info is None:
                pass
            else:
                for mqti in mysql_caseStep_info:
                    caseSteps=caseSteps+'\n'+mqti.content
                    expectations =expectations + '\n' + mqti.expectation

                cases_info[count]['caseStep'] = caseSteps
                cases_info[count]['expectation'] = expectations
        count+=1

    response=download(cases_info)

    return response

def download(cases_info):
    header_list=cases_info
    excel = pd.DataFrame(header_list)#二维数组，对应表头的相应数据
    excel.columns = ['编号','目录','标题','等级','前置条件','测试步骤','预期结果','附件']  #表头 [xx,xx,xx,xx]

    file = BytesIO()
    writer = pd.ExcelWriter(file, engine='xlsxwriter')
    excel.to_excel(writer,sheet_name='TestCase',index=False)

    #定义excle样式

    workbook = writer.book
    worksheet = writer.sheets['TestCase']
    # Add a header format.
    header_format = workbook.add_format({
        'bold': True,  # 字体加粗
        'text_wrap': True,  # 是否自动换行
        'valign': 'top',  # 垂直对齐方式
        'align': 'right',  # 水平对齐方式
        'fg_color': '#D7E4BC',  # 单元格背景颜色
        'border': 2})  # 单元格边框宽度
    other_format = workbook.add_format({
        'bold': False,  # 字体加粗
        'text_wrap': True,  # 是否自动换行
        'valign': 'top',  # 垂直对齐方式
        'align': 'right',  # 水平对齐方式
        'fg_color': '',  # 单元格背景颜色
        'border': 2})  # 单元格边框宽度
    yellow = workbook.add_format({'fg_color': '#FFEE99'})
    green = workbook.add_format({'fg_color': '#2dB054'})

    # Write the column headers with the defined format.
    for col_num, value in enumerate(excel.columns.values):
        if col_num % 2 == 0:
            worksheet.write(0, col_num, value, header_format)
        else:
            worksheet.write(0, col_num, value, header_format)

    # Write the row with the defined format.
    for index, value in excel.iterrows():
        # print(index, " -- > ", value.values)
        if index % 2 == 0:
            worksheet.write(index + 1, 0, value[0], header_format)
        else:
            worksheet.write(index + 1, 0, value[0], yellow)

    worksheet.set_column("A:C", 16)
    format2 = workbook.add_format({'bold': True, 'align': 'vcenter', 'valign': 'top', 'text_wrap': True})
    worksheet.set_row(0, cell_format=format2)
    # Close the Pandas Excel writer and output the Excel file.
    writer.save()

    response = Response(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    #下载文件命名，仅支持xlsx格式
    time.time()
    times=str(int(round(time.time() * 1000)))
    execl_name = '测试用例'+times+'.xlsx'
    response.headers["Content-disposition"] = 'attachment; filename=%s' % execl_name.encode().decode('latin-1')
    response.data = file.getvalue()
    return response
