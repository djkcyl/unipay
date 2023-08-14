# UniPay: 联合收款码封装

🌟 **UniPay** 是一个简洁高效的工具，封装了微信和支付宝的联合收款码，使得收款更加方便和高效。

## 🔍 项目介绍

**UniPay** 是一个针对微信和支付宝收款码进行封装的工具，旨在简化和统一收款流程，提供一种简洁的方式为你的业务接收付款。

## 📋 功能特性

- [x] 支持微信和支付宝收款码。
- [x] 支持自动跳转到收款码页面，PC 端展示双端收款码图片。
- [ ] 支持自定义收款码 ID。
- [ ] 支持自定义收款码样式。

## 📦 安装

通过 `pip` 进行安装:

```shell
pip install unipay
```

## 🚀 使用方法

启动 **UniPay**:

```shell
unipay
```

- 访问 [http://127.0.0.1:8600/docs](http://127.0.0.1:8600/docs) 查看 API 文档。
- 使用 `create_unipay` 接口生成联合收款码。
- 访问 [http://127.0.0.1:8600/xxxxxxxx](.) 查看收款码。

🖼️ **预览**:

![UniPay Preview](https://github.com/djkcyl/unipay/assets/59153990/2275fd12-fc5c-4f75-8b33-2b8fd8046be4)

## ⚠️ 注意事项

- 目前项目正在开发中，暂未提供任何配置。
- 尚未提供设置和生成 ID 的方式。
- 建议访问 [http://127.0.0.1:8600/docs](http://127.0.0.1:8600/docs) 查看 API 文档，并手动生成。
- **不建议在生产环境中使用。**
