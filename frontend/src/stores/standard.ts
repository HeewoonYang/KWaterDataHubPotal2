import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { PageRequest } from '@/types/common'
import type { StdWord, StdDomain, StdTerm, StdCode } from '@/types/standard'
import { wordApi, domainApi, termApi, codeApi } from '@/api/standard.api'

export const useStandardStore = defineStore('standard', () => {
  // 단어사전
  const words = ref<StdWord[]>([])
  const wordsTotal = ref(0)
  const wordsLoading = ref(false)

  async function fetchWords(params?: PageRequest) {
    wordsLoading.value = true
    try {
      const res = await wordApi.list(params)
      words.value = res.data.items
      wordsTotal.value = res.data.total
    } finally {
      wordsLoading.value = false
    }
  }

  // 도메인사전
  const domains = ref<StdDomain[]>([])
  const domainsTotal = ref(0)
  const domainsLoading = ref(false)

  async function fetchDomains(params?: PageRequest) {
    domainsLoading.value = true
    try {
      const res = await domainApi.list(params)
      domains.value = res.data.items
      domainsTotal.value = res.data.total
    } finally {
      domainsLoading.value = false
    }
  }

  // 용어사전
  const terms = ref<StdTerm[]>([])
  const termsTotal = ref(0)
  const termsLoading = ref(false)

  async function fetchTerms(params?: PageRequest) {
    termsLoading.value = true
    try {
      const res = await termApi.list(params)
      terms.value = res.data.items
      termsTotal.value = res.data.total
    } finally {
      termsLoading.value = false
    }
  }

  // 코드사전
  const codes = ref<StdCode[]>([])
  const codesTotal = ref(0)
  const codesLoading = ref(false)

  async function fetchCodes(params?: PageRequest) {
    codesLoading.value = true
    try {
      const res = await codeApi.list(params)
      codes.value = res.data.items
      codesTotal.value = res.data.total
    } finally {
      codesLoading.value = false
    }
  }

  return {
    words, wordsTotal, wordsLoading, fetchWords,
    domains, domainsTotal, domainsLoading, fetchDomains,
    terms, termsTotal, termsLoading, fetchTerms,
    codes, codesTotal, codesLoading, fetchCodes,
  }
})
