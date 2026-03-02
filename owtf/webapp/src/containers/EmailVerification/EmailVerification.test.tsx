import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import { EmailSendPage } from "./index";
import { fromJS } from "immutable";

import {
  emailSendSuccess,
  emailSendFail,
  emailVerificationSuccess,
  emailVerificationFail
} from "./actions";

import {
  EMAIL_SEND_START,
  EMAIL_SEND_SUCCESS,
  EMAIL_SEND_FAIL,
  EMAIL_VERIFICATION_START,
  EMAIL_VERIFICATION_SUCCESS,
  EMAIL_VERIFICATION_FAIL
} from "./constants";

import { postEmailToGenerateAPI, postToVerificationAPI } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { emailSendReducer, emailVerificationReducer } from "./reducer";

describe("EmailVerification component", () => {
  describe("Testing dumb email verification component", () => {
    let wrapper;
    let props;
    beforeEach(() => {
      props = {
        onResend: jest.fn(),
        email: "test_user@test.com"
      };
      wrapper = shallow(<EmailSendPage {...props} />);
    });
    it("Should have correct prop-types", () => {
      const expectedProps = {
        onResend: () => {},
        email: "test_user@test.com"
      };
      const propsErr = checkProps(EmailSendPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "emailSendPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      const heading = wrapper.find("withTheme(Heading)");
      const paragraph = wrapper.find("withTheme(Paragraph)");
      const button = wrapper.find("withTheme(Button)");

      expect(heading.length).toBe(1);
      expect(heading.at(0).props().children).toEqual("Email Sent");
      expect(paragraph.length).toBe(4);
      expect(paragraph.at(0).props().children).toEqual(
        "We have sent a mail to verify your email address."
      );
      expect(paragraph.at(3).props().children).toEqual(
        "If you don't find it in your inbox, check spam folder."
      );
      expect(button.length).toBe(1);
      expect(button.at(0).props().children).toEqual("Resend");
    });

    it("Should call onResend on Resend button click", () => {
      expect(props.onResend.mock.calls.length).toBe(0);
      const resendButton = wrapper.find("withTheme(Button)");
      resendButton.simulate("click");
      expect(props.onResend.mock.calls.length).toBe(1);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing postEmailToGenerateAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: EMAIL_SEND_START,
          email: "test_user@test.com"
        };
      });

      it("Should send an email in case of success", async () => {
        const successData = {
          status: "success",
          data: { status: "success", message: "Email send successful" }
        };

        const dispatchedActions = [];
        api.confirmEmailGenerateAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postEmailToGenerateAPI, fakeAction).done;
        expect(api.confirmEmailGenerateAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          emailSendSuccess(successData["data"]["message"])
        );
      });

      it("Should handle send email error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";

        api.confirmEmailGenerateAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postEmailToGenerateAPI, fakeAction).done;
        expect(api.confirmEmailGenerateAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(emailSendFail(error));
      });
    });

    describe("Testing postToVerificationAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: EMAIL_VERIFICATION_START,
          link: "test_link"
        };
      });

      it("Should verify a link in case of success", async () => {
        const successData = {
          status: "success",
          data: { status: "success", message: "Email Verified" }
        };

        const dispatchedActions = [];
        api.verifyEmailGenerateAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postToVerificationAPI, fakeAction).done;
        expect(api.verifyEmailGenerateAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          emailVerificationSuccess(successData["data"]["message"])
        );
      });

      it("Should handle link verification error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.verifyEmailGenerateAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postToVerificationAPI, fakeAction).done;
        expect(api.verifyEmailGenerateAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(emailVerificationFail(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing emailSendReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          error: false,
          loading: false
        };
      });

      it("Should return the initial state", () => {
        const newState = emailSendReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle EMAIL_SEND_START", () => {
        const newState = emailSendReducer(undefined, {
          type: EMAIL_SEND_START
        });

        expect(newState.toJS()).toEqual({
          loading: true,
          error: false
        });
      });

      it("Should handle EMAIL_SEND_SUCCESS", () => {
        const newState = emailSendReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: EMAIL_SEND_SUCCESS
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle EMAIL_SEND_FAIL", () => {
        const err = "Test sessions loading error";
        const newState = emailSendReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: EMAIL_SEND_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err
        });
      });
    });
    describe("Testing emailVerificationReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          error: false,
          loading: false
        };
      });

      it("Should return the initial state", () => {
        const newState = emailVerificationReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle EMAIL_VERIFICATION_START", () => {
        const link = "test_user_link";
        const newState = emailVerificationReducer(undefined, {
          type: EMAIL_VERIFICATION_START,
          link: link
        });

        expect(newState.toJS()).toEqual({
          loading: true,
          error: false
        });
      });

      it("Should handle EMAIL_VERIFICATION_SUCCESS", () => {
        const msg = "Email Verified";
        const newState = emailVerificationReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: EMAIL_VERIFICATION_SUCCESS,
            msg: msg
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false
        });
      });

      it("Should handle EMAIL_VERIFICATION_FAIL", () => {
        const err = "Test sessions loading error";
        const newState = emailVerificationReducer(
          fromJS({
            loading: true,
            error: true
          }),
          {
            type: EMAIL_VERIFICATION_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err
        });
      });
    });
  });
});
