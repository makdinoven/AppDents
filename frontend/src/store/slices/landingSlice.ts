import { createSlice, PayloadAction } from "@reduxjs/toolkit";

interface StateProps {
  newPrice: number;
  oldPrice: number;
  isModalOpen: boolean;
}

const initialState: StateProps = {
  newPrice: 0,
  oldPrice: 0,
  isModalOpen: false,
};

const landingSlice = createSlice({
  name: "landing",
  initialState,
  reducers: {
    setPrices(
      state,
      action: PayloadAction<{ newPrice: number; oldPrice: number }>,
    ) {
      state.newPrice = action.payload.newPrice;
      state.oldPrice = action.payload.oldPrice;
    },
    openModal(state) {
      state.isModalOpen = true;
    },
    closeModal(state) {
      state.isModalOpen = false;
    },
  },
});

export const { setPrices, openModal, closeModal } = landingSlice.actions;
export const landingReducer = landingSlice.reducer;
