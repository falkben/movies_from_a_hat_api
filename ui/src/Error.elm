module Error exposing (Error, configFailure, message)

{-| The Error module provides utilities for handling common application failure
modes. It's mostly intended for cases where there's no way for the app to
recover locally, and we just have to log the failure and display an error message
-}

import Http


type Error
    = ConfigFailure Http.Error


configFailure : Http.Error -> Error
configFailure error =
    ConfigFailure error


message : Error -> String
message error =
    case error of
        ConfigFailure httpErr ->
            httpErrorMessage "Failed to fetch API configuration because:" httpErr


httpErrorMessage : String -> Http.Error -> String
httpErrorMessage description error =
    description
        ++ "\n"
        ++ (case error of
                Http.BadBody bodyErr ->
                    "I could not understand the data sent by the server:\n" ++ bodyErr

                Http.NetworkError ->
                    "The network connection is down."

                Http.Timeout ->
                    "The remote server never responded."

                Http.BadStatus 403 ->
                    "The server said we do not have permission to access the data."

                Http.BadStatus 401 ->
                    "Our session has expired, a refresh may resolve the problem."

                Http.BadStatus status ->
                    if status >= 500 && status <= 599 then
                        "The remote server had an internal failure."

                    else
                        "The server responded with a status I don't recognize."

                Http.BadUrl urlProblem ->
                    "I seem to be using a bad URL to talk to the server:\n"
                        ++ urlProblem
                        ++ "\nThis is probably a bug."
           )
