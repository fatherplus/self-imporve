import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

interface ErrorComponentProps {
  /**
   * 错误页面标题，默认为 "Error"
   */
  title?: string
  /**
   * 错误页面描述文本，默认为 "Something went wrong. Please try again."
   */
  description?: string
  /**
   * 返回首页的链接目标，默认为 "/"
   */
  homeUrl?: string
  /**
   * 返回按钮文本，默认为 "Go Home"
   */
  buttonText?: string
}

const ErrorComponent = ({
  title = "Error",
  description = "Something went wrong. Please try again.",
  homeUrl = "/",
  buttonText = "Go Home",
}: ErrorComponentProps = {}) => {
  return (
    <div
      className="flex min-h-screen items-center justify-center flex-col p-4"
      data-testid="error-component"
    >
      <div className="flex items-center z-10">
        <div className="flex flex-col ml-4 items-center justify-center p-4">
          <span className="text-6xl md:text-8xl font-bold leading-none mb-4">
            {title}
          </span>
          <span className="text-2xl font-bold mb-2">Oops!</span>
        </div>
      </div>

      <p className="text-lg text-muted-foreground mb-4 text-center z-10">
        {description}
      </p>
      <Link to={homeUrl}>
        <Button>{buttonText}</Button>
      </Link>
    </div>
  )
}

export default ErrorComponent
