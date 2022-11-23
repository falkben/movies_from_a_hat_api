module Auth exposing (User, onPageLoad)

{-| The Auth module defines what the app should do when a user tries to access
a page that requires authentication

@docs User, onPageLoad

-}

import Auth.Action exposing (loadPageWithUser, showLoadingPage)
import Data.User as User
import Error exposing (Error)
import Html
import Route exposing (Route)
import Shared
import View exposing (View)


{-| Signed-in user data. This data will be passed to pages that require
authentication to render. Pages that require authn can be identified by the
fact that they take this type as the first argument to their `page` function.
-}
type alias User =
    User.User


{-| Runs when the user vistis a page requiring authentication. The value
returned from this will determine what the app does. Broadly speaking it can:

  - Navigate to an authentication interface of some kind
  - Return a [User](#User), enabling the page to render
  - Display a loading view

-}
onPageLoad : Shared.Model -> Route () -> Auth.Action.Action User
onPageLoad shared _ =
    case shared.user of
        User.Loading ->
            showLoadingPage loadingView

        User.Loaded user ->
            loadPageWithUser user

        User.Failed err ->
            showLoadingPage (failureView err)


loadingView : View Never
loadingView =
    { title = "Movies From a Hat"
    , body = [ Html.text "Loading..." ]
    }


failureView : Error -> View Never
failureView error =
    { title = "Oops!"
    , body =
        [ Html.pre []
            [ Html.text (Error.message error)
            ]
        ]
    }
