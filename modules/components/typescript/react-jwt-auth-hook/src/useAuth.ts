/**
 * React JWT Auth Hook
 *
 * 通用 JWT 认证 hook，基于 TanStack Query。
 *
 * 使用方式：
 *   1. 替换 LoginService/UsersService 为你的 API 服务
 *   2. 配置 tokenStorageKey 和 redirectPaths
 *   3. 在 App 入口调用 setupAuthErrorHandler
 *
 * 适配点：
 *   - loginFn: 登录 API 函数，返回 { access_token: string }
 *   - userFn: 获取当前用户 API 函数
 *   - signupFn: 注册 API 函数
 *   - showErrorToast: 错误提示函数
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

// ============================================================
// 适配点：替换以下类型和服务为你的实际实现
// ============================================================

// 登录表单数据类型
interface AccessToken {
  username: string
  password: string
}

// 用户公开信息类型
interface UserPublic {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  full_name: string | null
}

// 注册表单数据类型
interface UserRegister {
  email: string
  password: string
  full_name?: string
}

// 适配点：替换为你的 API 服务
// import { LoginService, UsersService } from "@/client"

const TOKEN_STORAGE_KEY = "access_token"

export const isLoggedIn = (): boolean => {
  return localStorage.getItem(TOKEN_STORAGE_KEY) !== null
}

/**
 * JWT 认证 hook。
 *
 * @param loginFn - 登录函数，接收表单数据，返回 { access_token }
 * @param userFn - 获取当前用户函数
 * @param signupFn - 注册函数
 * @param showErrorToast - 错误提示函数
 */
const useAuth = (config: {
  loginFn: (data: AccessToken) => Promise<{ access_token: string }>
  userFn: () => Promise<UserPublic>
  signupFn?: (data: UserRegister) => Promise<UserPublic>
  showErrorToast: (msg: string) => void
}) => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // 当前用户查询
  const { data: user } = useQuery<UserPublic | null, Error>({
    queryKey: ["currentUser"],
    queryFn: config.userFn,
    enabled: isLoggedIn(),
  })

  // 注册 mutation
  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) => {
      if (!config.signupFn) throw new Error("signupFn not configured")
      return config.signupFn(data)
    },
    onSuccess: () => {
      navigate({ to: "/login" })
    },
    onError: (err: Error) => {
      config.showErrorToast(extractErrorMessage(err))
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  // 登录
  const login = async (data: AccessToken) => {
    const response = await config.loginFn(data)
    localStorage.setItem(TOKEN_STORAGE_KEY, response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: Error) => {
      config.showErrorToast(extractErrorMessage(err))
    },
  })

  // 登出
  const logout = () => {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
    navigate({ to: "/login" })
  }

  return { signUpMutation, loginMutation, logout, user }
}

export default useAuth

// ============================================================
// 错误处理工具
// ============================================================

function extractErrorMessage(err: unknown): string {
  if (err instanceof Error && "body" in err) {
    const body = (err as any).body
    const detail = body?.detail
    if (Array.isArray(detail) && detail.length > 0) {
      return detail[0].msg
    }
    if (typeof detail === "string") return detail
  }
  if (err instanceof Error) return err.message
  return "Something went wrong."
}

/**
 * 配置 QueryClient 全局 401/403 错误处理。
 * 在 App 入口调用。
 *
 * 示例：
 *   import { QueryClient, QueryCache, MutationCache } from "@tanstack/react-query"
 *
 *   const handleApiError = setupAuthErrorHandler()
 *   const queryClient = new QueryClient({
 *     queryCache: new QueryCache({ onError: handleApiError }),
 *     mutationCache: new MutationCache({ onError: handleApiError }),
 *   })
 */
export function setupAuthErrorHandler() {
  return (error: Error) => {
    if (
      error &&
      "status" in error &&
      [401, 403].includes((error as any).status)
    ) {
      localStorage.removeItem(TOKEN_STORAGE_KEY)
      window.location.href = "/login"
    }
  }
}
