<template>
  <view class="page">
    <view class="header card">
      <text class="title">三骰猜大小</text>
      <view class="balance-row">
        <text class="label">筹码</text>
        <text class="balance">{{ balance }}</text>
      </view>
    </view>

    <view class="dice-area card">
      <view class="dice-row">
        <view
          v-for="(d, i) in displayDice"
          :key="i"
          class="die"
          :class="{ rolling: rolling }"
        >
          <text class="die-num">{{ d }}</text>
        </view>
      </view>
      <text v-if="lastSum !== null" class="sum-text">总和：{{ lastSum }}</text>
      <text v-if="lastMessage" class="result-text">{{ lastMessage }}</text>
    </view>

    <view class="card">
      <text class="section-title">选择玩法</text>
      <view class="bet-grid">
        <view
          v-for="item in betOptions"
          :key="item.type"
          class="bet-btn"
          :class="{ active: betType === item.type }"
          @click="betType = item.type"
        >
          <text class="bet-name">{{ item.label }}</text>
          <text class="bet-hint">{{ item.hint }}</text>
        </view>
      </view>
    </view>

    <view class="card">
      <text class="section-title">下注金额</text>
      <view class="amount-row">
        <button class="chip" size="mini" @click="adjustAmount(-50)">-50</button>
        <input
          class="amount-input"
          type="number"
          v-model.number="amount"
          @blur="clampAmount"
        />
        <button class="chip" size="mini" @click="adjustAmount(50)">+50</button>
      </view>
      <view class="quick-chips">
        <text
          v-for="n in quickAmounts"
          :key="n"
          class="quick"
          @click="amount = n"
        >{{ n }}</text>
      </view>
    </view>

    <button class="play-btn" :disabled="loading || rolling" @click="onPlay">
      {{ loading ? '开盅中…' : '开盅' }}
    </button>

    <view class="card rules">
      <text class="section-title">规则</text>
      <text class="rule-line">大：总和 11～17｜小：总和 4～10</text>
      <text class="rule-line">单：总和为奇｜双：总和为偶</text>
      <text class="rule-line">豹子（三同）通杀；3 点 / 18 点押大小判负</text>
      <text class="rule-line">赔率 1:1，初始筹码 10000</text>
    </view>

    <view v-if="history.length" class="card history">
      <text class="section-title">最近记录</text>
      <view v-for="(h, idx) in history" :key="idx" class="hist-item">
        <text>{{ h.time }} [{{ h.dice.join(',') }}] {{ h.sum }} 押{{ h.betLabel }}
          <text :class="h.win ? 'win' : 'lose'">{{ h.win ? '赢' : '输' }}</text>
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { initGame, fetchStatus, playRound, getToken, setToken } from '@/utils/api.js'

const balance = ref(0)
const betType = ref('big')
const amount = ref(100)
const loading = ref(false)
const rolling = ref(false)
const displayDice = ref([1, 1, 1])
const lastSum = ref(null)
const lastMessage = ref('')
const history = ref([])

const quickAmounts = [50, 100, 200, 500, 1000]

const betOptions = [
  { type: 'big', label: '大', hint: '11-17' },
  { type: 'small', label: '小', hint: '4-10' },
  { type: 'odd', label: '单', hint: '奇数' },
  { type: 'even', label: '双', hint: '偶数' },
]

function clampAmount() {
  let n = Number(amount.value) || 10
  if (n < 10) n = 10
  if (n > 5000) n = 5000
  amount.value = Math.floor(n)
}

function adjustAmount(delta) {
  amount.value = Math.max(10, Math.min(5000, (Number(amount.value) || 0) + delta))
}

async function ensureSession() {
  if (!getToken()) {
    const res = await initGame()
    setToken(res.token)
    balance.value = res.balance
    return
  }
  try {
    const res = await fetchStatus()
    balance.value = res.balance
    history.value = res.history || []
    if (res.last) {
      displayDice.value = res.last.dice
      lastSum.value = res.last.sum
    }
  } catch {
    const res = await initGame()
    setToken(res.token)
    balance.value = res.balance
  }
}

function rollAnimation(finalDice) {
  return new Promise((resolve) => {
    rolling.value = true
    let ticks = 0
    const timer = setInterval(() => {
      displayDice.value = [
        Math.floor(Math.random() * 6) + 1,
        Math.floor(Math.random() * 6) + 1,
        Math.floor(Math.random() * 6) + 1,
      ]
      ticks += 1
      if (ticks >= 12) {
        clearInterval(timer)
        displayDice.value = finalDice
        rolling.value = false
        resolve()
      }
    }, 80)
  })
}

async function onPlay() {
  if (!betType.value) {
    uni.showToast({ title: '请选择玩法', icon: 'none' })
    return
  }
  clampAmount()
  if (amount.value > balance.value) {
    uni.showToast({ title: '余额不足', icon: 'none' })
    return
  }

  loading.value = true
  lastMessage.value = ''
  try {
    const res = await playRound(betType.value, amount.value)
    await rollAnimation(res.result.dice)
    balance.value = res.balance
    lastSum.value = res.result.sum
    lastMessage.value = res.message
    history.value = [res.result, ...history.value].slice(0, 10)
    uni.showToast({
      title: res.result.win ? '恭喜赢了' : '再接再厉',
      icon: 'none',
    })
  } catch (e) {
    uni.showToast({ title: e.message || '失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  ensureSession().catch((e) => {
    uni.showToast({ title: e.message || '初始化失败', icon: 'none' })
  })
})
</script>

<style scoped>
.page {
  padding: 24rpx;
  padding-bottom: 48rpx;
}
.card {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 20rpx;
  padding: 28rpx;
  margin-bottom: 24rpx;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.header .title {
  font-size: 40rpx;
  font-weight: 700;
  color: #ffd666;
}
.balance-row {
  margin-top: 16rpx;
  display: flex;
  align-items: baseline;
  gap: 16rpx;
}
.balance {
  font-size: 48rpx;
  font-weight: 700;
  color: #fff;
}
.label {
  font-size: 26rpx;
  color: #aaa;
}
.dice-row {
  display: flex;
  justify-content: center;
  gap: 24rpx;
  margin: 16rpx 0;
}
.die {
  width: 120rpx;
  height: 120rpx;
  background: linear-gradient(145deg, #fff 0%, #e8e8e8 100%);
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(0, 0, 0, 0.35);
}
.die.rolling {
  transform: scale(1.05);
}
.die-num {
  font-size: 56rpx;
  font-weight: 800;
  color: #c41e3a;
}
.sum-text {
  display: block;
  text-align: center;
  font-size: 32rpx;
  color: #ffd666;
  margin-top: 8rpx;
}
.result-text {
  display: block;
  text-align: center;
  font-size: 26rpx;
  color: #ccc;
  margin-top: 12rpx;
  line-height: 1.5;
}
.section-title {
  font-size: 28rpx;
  color: #bbb;
  margin-bottom: 20rpx;
  display: block;
}
.bet-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20rpx;
}
.bet-btn {
  padding: 24rpx;
  border-radius: 16rpx;
  background: rgba(0, 0, 0, 0.25);
  border: 2px solid transparent;
  text-align: center;
}
.bet-btn.active {
  border-color: #ffd666;
  background: rgba(255, 214, 102, 0.15);
}
.bet-name {
  font-size: 36rpx;
  font-weight: 700;
  display: block;
}
.bet-hint {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
  display: block;
}
.amount-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}
.amount-input {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12rpx;
  padding: 16rpx 20rpx;
  color: #fff;
  text-align: center;
  font-size: 32rpx;
}
.chip {
  background: #444 !important;
  color: #fff !important;
}
.quick-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
  margin-top: 20rpx;
}
.quick {
  padding: 12rpx 28rpx;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 999rpx;
  font-size: 26rpx;
}
.play-btn {
  margin: 8rpx 0 24rpx;
  background: linear-gradient(90deg, #c41e3a, #e85d04) !important;
  color: #fff !important;
  border: none;
  font-size: 34rpx;
  font-weight: 700;
  border-radius: 999rpx;
}
.play-btn[disabled] {
  opacity: 0.6;
}
.rules .rule-line {
  display: block;
  font-size: 24rpx;
  color: #aaa;
  line-height: 1.8;
}
.hist-item {
  font-size: 22rpx;
  color: #bbb;
  padding: 8rpx 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.win {
  color: #52c41a;
}
.lose {
  color: #ff4d4f;
}
</style>
