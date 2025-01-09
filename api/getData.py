from flask import Flask, jsonify, request
import pandas as pd
from flask_cors import CORS
import os

app = Flask(__name__)
app.json.ensure_ascii = False  # 这里设置全局的 JSON 编码选项
CORS(app)  # 启用CORS以允许前端访问


def get_latest_csv():
    # 获取当前目录下所有文件
    files = [
        f for f in os.listdir(".") if f.startswith("app_titles_") and f.endswith(".csv")
    ]

    if not files:
        raise FileNotFoundError("没有找到app_titles_开头的CSV文件")

    # 按文件名排序，获取最新的文件
    latest_file = sorted(files)[-1]
    return latest_file


@app.route("/api/apps/search", methods=["GET"])
def search_apps():
    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search_term = request.args.get("q", "")

        print(
            f"搜索参数: page={page}, per_page={per_page}, q={search_term}"
        )  # 调试信息

        # 读取最新的CSV文件
        latest_file = get_latest_csv()
        print(f"准备读取文件: {latest_file}")  # 调试信息

        df = pd.read_csv(latest_file)

        # 搜索过滤
        if search_term:
            df = df[df["title"].str.contains(search_term, case=False, na=False)]

        # 计算分页
        total = len(df)
        start = (page - 1) * per_page
        end = start + per_page

        # 切片获取当前页数据
        apps_list = df.iloc[start:end].to_dict("records")

        response_data = {
            "status": "success",
            "data": apps_list,
            "total": total,
            "page": page,
            "per_page": per_page,
        }

        print(f"返回数据: {response_data}")  # 调试信息
        return jsonify(response_data)

    except Exception as e:
        error_response = {"status": "error", "message": str(e)}
        print(f"错误: {error_response}")  # 调试信息
        return jsonify(error_response), 500


if __name__ == "__main__":
    # 启动 Web 服务器
    app.run(debug=True, port=5000)
