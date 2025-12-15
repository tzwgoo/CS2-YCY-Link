/**
 * YCY IM 客户端 - 基于腾讯云 IM SDK
 * 在前端直接连接和发送消息
 */

import TencentCloudChat from '@tencentcloud/chat'

class YCYIMClient {
  constructor() {
    this.apiBase = 'https://suo.jiushu1234.com/api.php'
    this.chat = null
    this.uid = null
    this.userId = null
    this.token = null
    this.appId = null
    this.sign = null
    this.isConnected = false
    this.messageQueue = []
    this.TIM = TencentCloudChat
  }

  /**
   * 初始化并连接 IM
   * @param {string} uid - 用户 ID（不带 game_ 前缀）
   * @param {string} token - Token
   */
  async connect(uid, token) {
    try {
      console.log('正在连接 YCY IM...', { uid, token: token.substring(0, 10) + '...' })

      // 保存配置
      this.userId = uid
      this.uid = `game_${uid}`
      this.token = token

      // 1. 获取 IM 签名
      const signData = await this.requestGameSign()
      if (!signData) {
        throw new Error('获取 IM 签名失败')
      }

      this.appId = signData.appid
      this.sign = signData.sign

      console.log('✓ 获取签名成功', { appId: this.appId })

      // 2. 初始化腾讯 IM SDK
      this.chat = TencentCloudChat.create({
        SDKAppID: parseInt(this.appId)
      })

      // 设置日志级别
      this.chat.setLogLevel(1) // 0: 普通, 1: 发布, 2: 告警, 3: 错误

      // 3. 注册事件监听
      this.registerEvents()

      // 4. 登录 IM
      const loginRes = await this.chat.login({
        userID: this.uid,
        userSig: this.sign
      })

      console.log('✓ IM 登录成功', loginRes)

      this.isConnected = true

      // 5. 发送队列中的消息
      await this.flushMessageQueue()

      return {
        success: true,
        message: 'IM 连接成功',
        data: {
          uid: this.uid,
          userId: this.userId,
          appId: this.appId
        }
      }
    } catch (error) {
      console.error('✗ IM 连接失败', error)
      this.isConnected = false
      return {
        success: false,
        message: error.message || 'IM 连接失败'
      }
    }
  }

  /**
   * 断开连接
   */
  async disconnect() {
    if (this.chat) {
      try {
        await this.chat.logout()
        console.log('✓ IM 已断开连接')
      } catch (error) {
        console.error('断开连接失败', error)
      }
    }
    this.isConnected = false
    this.chat = null
  }

  /**
   * 获取 IM 签名
   */
  async requestGameSign() {
    try {
      const response = await fetch(`${this.apiBase}/user/game_sign`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          uid: this.uid,
          token: this.token
        })
      })

      const result = await response.json()

      if (result.code === 1 && result.data) {
        return result.data
      } else {
        throw new Error(result.msg || '获取签名失败')
      }
    } catch (error) {
      console.error('请求签名失败', error)
      throw error
    }
  }

  /**
   * 注册 IM 事件监听
   */
  registerEvents() {
    // SDK 就绪
    this.chat.on(TencentCloudChat.EVENT.SDK_READY, () => {
      console.log('✓ IM SDK 就绪')
    })

    // SDK 未就绪
    this.chat.on(TencentCloudChat.EVENT.SDK_NOT_READY, () => {
      console.log('⚠ IM SDK 未就绪')
      this.isConnected = false
    })

    // 被踢下线
    this.chat.on(TencentCloudChat.EVENT.KICKED_OUT, () => {
      console.log('⚠ IM 被踢下线')
      this.isConnected = false
    })

    // 网络状态变化
    this.chat.on(TencentCloudChat.EVENT.NET_STATE_CHANGE, (event) => {
      console.log('网络状态:', event.data.state)
    })

    // 收到消息
    this.chat.on(TencentCloudChat.EVENT.MESSAGE_RECEIVED, (event) => {
      console.log('📩 收到消息', event.data)
    })

    // 错误
    this.chat.on(TencentCloudChat.EVENT.ERROR, (event) => {
      console.error('IM 错误', event.data)
    })
  }

  /**
   * 发送游戏指令
   * @param {string} commandId - 指令 ID
   */
  async sendCommand(commandId) {
    if (!this.isConnected) {
      console.warn('IM 未连接，消息已加入队列')
      this.messageQueue.push(commandId)
      return {
        success: false,
        message: 'IM 未连接，消息已加入队列'
      }
    }

    try {
      // 构造消息内容
      const messageText = JSON.stringify({
        code: 'game_cmd',
        id: commandId,
        token: this.token
      })

      // 创建文本消息
      const message = this.chat.createTextMessage({
        to: this.userId, // 目标用户 ID（不带 game_ 前缀）
        conversationType: TencentCloudChat.TYPES.CONV_C2C,
        payload: {
          text: messageText
        }
      })

      // 发送消息
      const sendRes = await this.chat.sendMessage(message)

      console.log('✓ 指令发送成功', {
        commandId,
        to: this.userId,
        message: messageText
      })

      return {
        success: true,
        message: '指令发送成功',
        data: sendRes
      }
    } catch (error) {
      console.error('✗ 指令发送失败', error)
      return {
        success: false,
        message: error.message || '指令发送失败'
      }
    }
  }

  /**
   * 发送队列中的消息
   */
  async flushMessageQueue() {
    if (this.messageQueue.length === 0) return

    console.log(`发送队列中的 ${this.messageQueue.length} 条消息`)

    while (this.messageQueue.length > 0) {
      const commandId = this.messageQueue.shift()
      await this.sendCommand(commandId)
      // 避免发送过快
      await new Promise(resolve => setTimeout(resolve, 100))
    }
  }

  /**
   * 获取连接状态
   */
  getStatus() {
    return {
      isConnected: this.isConnected,
      uid: this.uid,
      userId: this.userId,
      appId: this.appId,
      queueLength: this.messageQueue.length
    }
  }
}

// 创建全局单例
const imClient = new YCYIMClient()

export default imClient
